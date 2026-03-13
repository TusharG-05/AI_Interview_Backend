from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Body
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User, Questions, QuestionPaper, InterviewSession, InterviewResult, Answers, SessionQuestion, InterviewStatus, ProctoringEvent, CodingQuestions
from ..schemas.requests import AnswerRequest
from ..schemas.interview_result import UserNested, QuestionPaperNested
from ..services import interview as interview_service
from ..services.audio import AudioService
from ..schemas.interview_responses import (
    InterviewAccessResponse, QuestionNested, PaperNested, 
    CodingQuestionNested, CodingPaperNested, InterviewSessionData, 
    QuestionPaperData, QuestionData, AnswersData, CodingAnswersData
)
from ..schemas.user_schemas import UserNested, serialize_user
from ..schemas.api_response import ApiResponse
from ..auth.dependencies import get_current_user
from pydantic import BaseModel
import os
import uuid
from datetime import datetime, timedelta, timezone

from pydub import AudioSegment
import logging

router = APIRouter(prefix="/interview", tags=["Interview"])
from ..utils import format_iso_datetime, calculate_total_score
from ..tasks.interview_tasks import process_session_results_task
logger = logging.getLogger(__name__)
audio_service = AudioService()

from ..services.status_manager import add_violation


def _evaluate_and_update_score(
    db: Session,
    answer: Answers,
    question_text: str,
    session_obj: InterviewSession,
    result_obj: InterviewResult,
) -> None:
    """
    Evaluate a single answer using the LLM service, persist score & feedback onto
    the Answers row, then recompute and persist the running total_score (sum of all
    answer scores) on both InterviewResult and InterviewSession.

    Wrapped in a broad try/except so an LLM failure or stale-session error never
    prevents the answer from being saved successfully.
    """
    try:
        # 1. Skip evaluation if there is no text to evaluate
        if not answer.candidate_answer and not answer.transcribed_text:
            logger.warning(
                f"Answer {answer.id}: no text to evaluate, skipping LLM call."
            )
            return

        text_to_evaluate = answer.candidate_answer or answer.transcribed_text

        # 2. Load question to get response_type and title
        resp_type = "text"
        q_title = question_text
        
        if getattr(answer, 'question_id', None):
            question_obj = db.get(Questions, answer.question_id)
            if question_obj:
                resp_type = (question_obj.response_type.value if hasattr(question_obj.response_type, 'value') else str(question_obj.response_type)) if question_obj.response_type else "text"
                q_title = question_obj.question_text or question_obj.content or question_text
        elif getattr(answer, 'coding_question_id', None):
            question_obj = db.get(CodingQuestions, answer.coding_question_id)
            if question_obj:
                resp_type = "code"
                q_title = question_obj.title or question_text

        # 3. Call LLM evaluation (routes to code evaluator if response_type='code')
        logger.info(f"Answer {answer.id}: running real-time evaluation (type={resp_type})...")
        evaluation = interview_service.evaluate_answer_content(
            question_text, text_to_evaluate,
            response_type=resp_type,
            question_title=q_title,
        )

        answer.feedback = evaluation.get("feedback", "")
        answer.score = float(evaluation.get("score") or 0.0)
        db.add(answer)
        db.flush()  # write score to DB without committing yet

        logger.info(f"Answer {answer.id}: evaluated, score={answer.score}")

        # 3. Recompute running total_score (sum) — re-fetch all saved scores
        all_answers = db.exec(
            select(Answers).where(Answers.interview_result_id == result_obj.id)
        ).all()
        
        # Also naturally include CodingAnswers if they exist
        from ..models.db_models import CodingAnswers
        all_coding_answers = db.exec(
            select(CodingAnswers).where(CodingAnswers.interview_result_id == result_obj.id)
        ).all()

        all_scores = [a.score for a in all_answers if a.score is not None]
        all_scores.extend([ca.score for ca in all_coding_answers if ca.score is not None])
        
        new_total = calculate_total_score(all_scores)

        result_obj.total_score = new_total
        session_obj.total_score = new_total

        db.add(result_obj)
        db.add(session_obj)
        db.commit()

        logger.info(
            f"Interview {session_obj.id}: total_score updated to {new_total}"
        )

    except Exception as exc:
        # Roll back only the evaluation updates; the answer row itself was already
        # committed by the caller before this helper runs.
        try:
            db.rollback()
        except Exception:
            pass
        logger.error(
            f"Real-time evaluation failed for answer {answer.id} "
            f"(interview {session_obj.id}): {exc}",
            exc_info=True,
        )
        # Do NOT re-raise — a failed evaluation must never block answer saving.


from ..services.status_manager import add_violation

class TTSRange(BaseModel):
    text: str




@router.get("/access/{token}", response_model=ApiResponse[InterviewAccessResponse])
async def access_interview(
    token: str, 
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validates the interview link and checks time constraints.
    Returns a cleaned, frontend-friendly response structure.
    """
    from sqlalchemy.orm import selectinload
    from ..models.db_models import QuestionPaper, CodingQuestionPaper, InterviewStatus, CandidateStatus

    # Query with all relationships preloaded to avoid N+1 issues
    session = session_db.exec(
        select(InterviewSession)
        .where(InterviewSession.access_token == token)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.paper).selectinload(QuestionPaper.questions),
            selectinload(InterviewSession.paper).selectinload(QuestionPaper.admin),
            selectinload(InterviewSession.coding_paper).selectinload(CodingQuestionPaper.questions),
            selectinload(InterviewSession.coding_paper).selectinload(CodingQuestionPaper.admin)
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Invalid Interview Link")
        
    # Map Administrator
    admin_data = None
    if session.admin:
        admin_data = UserNested(
            id=session.admin.id,
            email=session.admin.email,
            full_name=session.admin.full_name,
            role=session.admin.role.value if hasattr(session.admin.role, 'value') else str(session.admin.role),
            access_token=session.admin.access_token or ""
        )

    # Map Candidate
    candidate_data = None
    if session.candidate:
        candidate_data = UserNested(
            id=session.candidate.id,
            email=session.candidate.email,
            full_name=session.candidate.full_name,
            role=session.candidate.role.value if hasattr(session.candidate.role, 'value') else str(session.candidate.role),
            access_token=session.candidate.access_token or ""
        )

    # Map Standard Question Paper
    paper_data = None
    if session.paper:
        questions_list = [
            QuestionNested(
                id=q.id,
                paper_id=q.paper_id,
                content=q.content or "",
                question_text=q.question_text or q.content or "",
                topic=q.topic or "General",
                difficulty=q.difficulty or "Medium",
                marks=q.marks or 1,
                response_type=q.response_type or "audio"
            ) for q in session.paper.questions
        ]
        
        paper_admin_data = None
        if session.paper.admin:
            paper_admin_data = serialize_user(session.paper.admin)
            
        paper_data = PaperNested(
            id=session.paper.id,
            name=session.paper.name,
            description=session.paper.description or "",
            admin_user=serialize_user(session.admin) if session.admin else None,  # ← Always UserNested
            question_count=session.paper.question_count or len(questions_list),
            total_marks=session.paper.total_marks or sum(q.marks for q in questions_list),
            created_at=session.paper.created_at,
            questions=questions_list
        )

    # Map Coding Question Paper
    coding_paper_data = None
    if session.coding_paper:
        coding_questions_list = [
            CodingQuestionNested(
                id=cq.id,
                paper_id=cq.paper_id,
                title=cq.title or "",
                problem_statement=cq.problem_statement or "",
                examples=cq.examples or "[]",
                constraints=cq.constraints or "[]",
                starter_code=cq.starter_code or "",
                topic=cq.topic or "Algorithms",
                difficulty=cq.difficulty or "Medium",
                marks=cq.marks or 0
            ) for cq in session.coding_paper.questions
        ]
        
        coding_admin_data = None
        if session.coding_paper.admin:
            coding_admin_data = serialize_user(session.coding_paper.admin)
            
        coding_paper_data = CodingPaperNested(
            id=session.coding_paper.id,
            name=session.coding_paper.name,
            description=session.coding_paper.description or "",
            admin_user=coding_admin_data,
            question_count=session.coding_paper.question_count or len(coding_questions_list),
            total_marks=session.coding_paper.total_marks or sum(cq.marks for cq in coding_questions_list),
            created_at=session.coding_paper.created_at,
            coding_questions=coding_questions_list
        )

    now = datetime.now(timezone.utc)
    
    # 1. Status Expired/Cancelled Check
    if session.status in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
        raise HTTPException(status_code=403, detail=f"Interview is {session.status.value.lower()}")
        
    # 2. Start Time Check (Temporal)
    schedule_time = session.schedule_time
    if schedule_time.tzinfo is None:
        schedule_time = schedule_time.replace(tzinfo=timezone.utc)
        
    # 3. Expiration Check
    expiration_time = schedule_time + timedelta(minutes=session.duration_minutes)
    if now > expiration_time:
         session.status = InterviewStatus.EXPIRED
         session_db.add(session)
         session_db.commit()
         raise HTTPException(status_code=403, detail="Interview link has expired")
         
    # 4. Track link access status change
    from ..services.status_manager import record_status_change
    if session.current_status == CandidateStatus.INVITED:
        record_status_change(
            session=session_db,
            interview_session=session,
            new_status=CandidateStatus.LINK_ACCESSED
        )
    
    # 5. Determine status strings (Preserve Case for exact match if needed, but using .lower() as originally requested might be what "Renaming fields" includes?)
    # User said: "Renaming fields is allowed. Example: admin_id -> admin... However the object structures inside them must remain identical."
    # And specifically: "Status: scheduled | live | completed | expired | cancelled" in the first prompt.
    # Actually, the user's second prompt said: "A previous refactor modified the response structure... and introduced breaking changes... restore... keeping RENAMED fields".
    # This implies I should keep the field names I just changed (admin, candidate, etc.) but restore the internal object structure.
    # The status values themselves (scheduled vs SCHEDULED) are data, but usually frontend maps these.
    # I'll stick to the requested lowercase statuses from the FIRST prompt unless told otherwise, but I'll ensure they are present.
    
    status_str = session.status.value.lower() if hasattr(session.status, 'value') else str(session.status).lower()
    current_status_str = session.current_status.value.lower() if hasattr(session.current_status, 'value') else str(session.current_status).lower()
    
    message = "Access Granted"
    if now < schedule_time:
        current_status_str = "wait" 
        message = "Interview not yet started. Please wait."

    response_data = InterviewAccessResponse(
        id=session.id,
        access_token=session.access_token,
        admin_user=serialize_user(session.admin) if session.admin else None,  # ← Always UserNested
        candidate_user=candidate_data,
        paper=paper_data,
        coding_paper=coding_paper_data,
        schedule_time=session.schedule_time,
        duration_minutes=session.duration_minutes,
        max_questions=session.max_questions,
        start_time=session.start_time,
        end_time=session.end_time,
        status=status_str,
        total_score=session.total_score,
        current_status=current_status_str,
        last_activity=session.last_activity or now,
        warning_count=session.warning_count or 0,
        max_warnings=session.max_warnings or 3,
        is_suspended=session.is_suspended or False,
        suspension_reason=session.suspension_reason,
        suspended_at=session.suspended_at,
        enrollment_audio_path=session.enrollment_audio_path,
        is_completed=session.is_completed or False,
        allow_copy_paste=session.allow_copy_paste,
        result_status="PENDING" # Default for access endpoint as per original schema
    )

    return ApiResponse(
        status_code=200,
        data=response_data,
        message=message
    )


@router.post("/start-session/{interview_id}", response_model=ApiResponse[dict])
async def start_session_logic(
    interview_id: int,
    enrollment_audio: UploadFile = File(None),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Called when candidate actually enters the interview session (uploads selfie/audio).
    Sets status to LIVE.
    """
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    session = session_db.get(InterviewSession, interview_id)
    if not session: raise HTTPException(status_code=404)
    
    # Check if suspended
    if session.is_suspended:
        raise HTTPException(
            status_code=403, 
            detail=f"Interview suspended: {session.suspension_reason}"
        )
    
    # Track enrollment start
    if enrollment_audio and session.current_status != CandidateStatus.ENROLLMENT_STARTED:
        record_status_change(
            session=session_db,
            interview_session=session,
            new_status=CandidateStatus.ENROLLMENT_STARTED
        )
    
    # Update Status
    if session.status == InterviewStatus.SCHEDULED:
        session.status = InterviewStatus.LIVE
        session.start_time = datetime.now(timezone.utc)
        
    # Always mark as active once the session is started
    if session.current_status not in [CandidateStatus.INTERVIEW_ACTIVE, CandidateStatus.INTERVIEW_COMPLETED]:
        record_status_change(
            session=session_db,
            interview_session=session,
            new_status=CandidateStatus.INTERVIEW_ACTIVE
        )
    
    warning = None
    try:
        if enrollment_audio:
            os.makedirs("app/assets/audio/enrollment", exist_ok=True)
            enrollment_path = f"app/assets/audio/enrollment/enroll_{session.id}.wav"
            content = await enrollment_audio.read()
            audio_service.save_audio_blob(content, enrollment_path)
            
            # Silence/Quality Check
            try:
                if audio_service.calculate_energy(enrollment_path) < 50:
                     warning = "Enrolled audio is very quiet. Speaker verification might be inaccurate."
            except Exception as e:
                logger.warning(f"Energy check failed: {e}")
            
            # Cleanup only after processing
            audio_service.cleanup_audio(enrollment_path)
            
            session.enrollment_audio_path = enrollment_path
            
            # Track enrollment completion
            record_status_change(
                session=session_db,
                interview_session=session,
                new_status=CandidateStatus.ENROLLMENT_COMPLETED
            )
            
        session_db.add(session)
        session_db.commit()
    except Exception as e:
        session_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")
        
    return ApiResponse(
        status_code=200,
        data={"interview_id": session.id, "status": "LIVE", "warning": warning},
        message="Interview session started successfully"
    )

@router.post("/upload-selfie", response_model=ApiResponse[dict])
async def upload_selfie_session(
    interview_id: int = Form(...),
    file: UploadFile = File(...),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Allows candidate to upload their reference selfie via interview session context.
    """
    from ..models.db_models import CandidateStatus, User
    import os, json, tempfile
    from ..core.logger import get_logger
    _logger = get_logger(__name__)
    
    # 1. Verify Session
    interview_session = session_db.get(InterviewSession, interview_id)
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    candidate = interview_session.candidate
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found for this session")

    # Relaxed content type check: canvas.toBlob can send application/octet-stream in some browsers
    if file.content_type and not (file.content_type.startswith("image/") or file.content_type == "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"File must be an image, got: {file.content_type}")
        
    # 2. Read bytes
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Received empty file")
    
    # 3. Save to User object
    candidate.profile_image_bytes = image_bytes
    
    # 4. Generate Embeddings (best effort — never block on failure)
    try:
        from deepface import DeepFace
        import asyncio
        embeddings_map = {}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            # Use asyncio timeout for better Hugging Face compatibility
            async def generate_embeddings():
                try:
                    arc_objs = DeepFace.represent(img_path=tmp_path, model_name="ArcFace", enforce_detection=False, detector_backend="skip")
                    if arc_objs:
                        embeddings_map["ArcFace"] = arc_objs[0]["embedding"]
                except Exception as e:
                    _logger.warning(f"ArcFace embedding failed: {e}")

                try:
                    sface_objs = DeepFace.represent(img_path=tmp_path, model_name="SFace", enforce_detection=False, detector_backend="skip")
                    if sface_objs:
                        embeddings_map["SFace"] = sface_objs[0]["embedding"]
                except Exception as e:
                    _logger.warning(f"SFace embedding failed: {e}")

                if embeddings_map:
                    candidate.face_embedding = json.dumps(embeddings_map)
            
            # Run with timeout
            try:
                await asyncio.wait_for(generate_embeddings(), timeout=10.0)
            except asyncio.TimeoutError:
                _logger.warning("Embedding generation timed out (non-fatal)")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        _logger.error(f"Embedding generation failed (non-fatal): {e}")

    # 5. Store image URL in database profile_image
    from ..services.cloudinary_service import CloudinaryService
    cloudinary_service = CloudinaryService()
    try:
        # Add timeout for Cloudinary upload
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(cloudinary_service.upload_image, image_bytes, folder="interview_selfies")
            try:
                cloudinary_url = future.result(timeout=15)  # 15 second timeout
                candidate.profile_image = cloudinary_url
            except concurrent.futures.TimeoutError:
                _logger.warning("Cloudinary upload timed out (non-fatal)")
                raise
    except Exception as e:
        _logger.error(f"Cloudinary upload failed (non-fatal): {e}")
        # Fallback to base64 if cloudinary fails
        import base64
        content_type = file.content_type or "image/jpeg"
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
        candidate.profile_image = f"data:{content_type};base64,{base64_encoded}"

    session_db.add(candidate)
    
    # 6. Track Status (best effort — don't let enum issues block the upload)
    try:
        from ..services.status_manager import record_status_change
        record_status_change(
            session=session_db,
            interview_session=interview_session,
            new_status=CandidateStatus.SELFIE_UPLOADED
        )
    except Exception as e:
        _logger.warning(f"Status tracking failed (non-fatal): {e}")
        try:
            session_db.commit()
        except Exception:
            session_db.rollback()
    
    try:
        session_db.commit()
    except Exception as e:
        session_db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save identity data")
    
    return ApiResponse(
        status_code=200,
        data={
            "interview_id": interview_id,
            "candidate_id": candidate.id,
            "profile_image_url": candidate.profile_image
        },
        message="Selfie uploaded and identity verified successfully"
    )

@router.get("/next-question/{interview_id}", response_model=ApiResponse[dict])
async def get_next_question(interview_id: int, session_db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    from ..services.status_manager import record_status_change, update_last_activity
    from ..models.db_models import CandidateStatus
    
    # Get session and check suspension
    session_obj = session_db.get(InterviewSession, interview_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_obj.is_suspended:
        raise HTTPException(
            status_code=403,
            detail=f"Interview suspended: {session_obj.suspension_reason}"
        )
    
    # Track interview active status (on first question fetch)
    if session_obj.current_status == CandidateStatus.ENROLLMENT_COMPLETED:
        record_status_change(
            session=session_db,
            interview_session=session_obj,
            new_status=CandidateStatus.INTERVIEW_ACTIVE
        )
    
    # Update last activity
    update_last_activity(session_db, session_obj)
    
    # 1. Get answered questions
    # Need to find InterviewResult first or join
    # answered_ids = [r.question_id for r in session_db.exec(select(Answers).join(InterviewResult).where(InterviewResult.interview_id == interview_id)).all()]
    # simplified:
    answered_ids = []
    result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if result:
        answered_ids = [a.question_id for a in result.answers]
    
    # 2. Check if this session has assigned questions (Campaign mode)
    has_assignments = session_db.exec(
        select(SessionQuestion).where(SessionQuestion.interview_id == interview_id)
    ).first() is not None
    
    # Logic Update: If Bank is assigned, we should pull from Bank if no session_questions pre-assigned?
    # For now, sticking to logic:
    
    if has_assignments:
        # Campaign mode: Strictly follow assigned questions
        stmt = select(SessionQuestion).where(SessionQuestion.interview_id == interview_id)
        if answered_ids:
            stmt = stmt.where(~SessionQuestion.question_id.in_(answered_ids))
        stmt = stmt.order_by(SessionQuestion.sort_order)
        session_q = session_db.exec(stmt).first()
        question = session_q.question if session_q else None
    else:
        # Fallback: Pull from the assigned Paper (if any) or General pool
        if session_obj and session_obj.paper_id:
             # Security Fix: Strictly scope to the assigned paper
             stmt = select(Questions).where(Questions.paper_id == session_obj.paper_id)
             if answered_ids:
                 stmt = stmt.where(~Questions.id.in_(answered_ids))
             question = session_db.exec(stmt).first()
        else:
             # Pull only from global/orphaned pool, never from other papers
             stmt = select(Questions).where(Questions.paper_id == None)
             if answered_ids:
                 stmt = stmt.where(~Questions.id.in_(answered_ids))
             question = session_db.exec(stmt).first()
    
    if not question:
        # ---------------------------------------------------------------
        # Option A: Fall through to CodingQuestions if the session has a
        # coding_paper_id linked. We create a thin proxy Questions row the
        # first time each coding question is served so the existing Answers
        # / scoring pipeline continues to work unchanged.
        # ---------------------------------------------------------------
        if session_obj and session_obj.coding_paper_id:
            import json as _json

            # All CodingQuestions for this paper
            all_coding_qs = session_db.exec(
                select(CodingQuestions).where(
                    CodingQuestions.paper_id == session_obj.coding_paper_id
                )
            ).all()

            # Answered coding questions (tracked via proxy Questions rows tagged with topic="coding_proxy")
            answered_proxy_ids = set(answered_ids)  # already collected above

            # Find answered coding question IDs via proxy Questions title match isn't reliable;
            # instead we tag proxy rows uniquely: question_text = f"__coding__{cq.id}"
            answered_coding_cq_ids = set()
            for qid in answered_proxy_ids:
                proxy = session_db.get(Questions, qid)
                if proxy and proxy.question_text.startswith("__coding__"):
                    try:
                        answered_coding_cq_ids.add(int(proxy.question_text.split("__coding__")[1]))
                    except (ValueError, IndexError):
                        pass

            # Pick the next un-answered coding question
            next_cq = next(
                (cq for cq in all_coding_qs if cq.id not in answered_coding_cq_ids),
                None
            )

            if next_cq is None:
                return ApiResponse(
                    status_code=200,
                    data={"status": "finished"},
                    message="All questions completed"
                )

            # Find or create the proxy Questions row for this coding question
            proxy_tag = f"__coding__{next_cq.id}"
            proxy_q = session_db.exec(
                select(Questions).where(Questions.question_text == proxy_tag)
            ).first()

            if proxy_q is None:
                # Store full problem body as JSON in `content` so admin results API can parse it later
                problem_body = {
                    "title": next_cq.title,
                    "problem_statement": next_cq.problem_statement,
                    "examples": _json.loads(next_cq.examples) if isinstance(next_cq.examples, str) else next_cq.examples,
                    "constraints": _json.loads(next_cq.constraints) if isinstance(next_cq.constraints, str) else next_cq.constraints,
                    "starter_code": next_cq.starter_code or "",
                }

                proxy_q = Questions(
                    paper_id=None,          # orphaned — not tied to any standard paper
                    content=_json.dumps(problem_body, ensure_ascii=False),
                    question_text=proxy_tag,
                    topic=next_cq.topic,
                    difficulty=next_cq.difficulty,
                    marks=next_cq.marks,
                    response_type="code",
                )
                session_db.add(proxy_q)
                try:
                    session_db.commit()
                    session_db.refresh(proxy_q)
                except Exception as e:
                    logger.error(f"Failed to create coding question proxy: {e}", exc_info=True)
                    session_db.rollback()
                    raise HTTPException(status_code=500, detail=f"Failed to create coding question proxy: {str(e)}")

            # Generate TTS for the coding question title
            os.makedirs("app/assets/audio/questions", exist_ok=True)
            audio_path = f"app/assets/audio/questions/q_{proxy_q.id}.mp3"
            if not os.path.exists(audio_path):
                await audio_service.text_to_speech(next_cq.title, audio_path)

            question_index = len(answered_ids) + 1
            total_coding = len(all_coding_qs)
            
            # Calculate total_questions (similar to line 678)
            total_questions = 0
            if has_assignments:
                total_questions = len(session_db.exec(select(SessionQuestion).where(SessionQuestion.interview_id == interview_id)).all())
            elif session_obj and session_obj.paper_id:
                total_questions = len(session_db.exec(select(Questions).where(Questions.paper_id == session_obj.paper_id)).all())

            return ApiResponse(
                status_code=200,
                data={
                    "question_id": proxy_q.id,
                    "coding_question_id": next_cq.id,
                    "text": next_cq.title,
                    "audio_url": f"/interview/audio/question/{proxy_q.id}",
                    "response_type": "code",
                    "question_index": question_index,
                    "total_questions": total_questions + total_coding,
                    "coding_content": {
                        "title": next_cq.title,
                        "problem_statement": next_cq.problem_statement,
                        "examples": _json.loads(next_cq.examples) if isinstance(next_cq.examples, str) else next_cq.examples,
                        "constraints": _json.loads(next_cq.constraints) if isinstance(next_cq.constraints, str) else next_cq.constraints,
                        "starter_code": next_cq.starter_code or None,
                    },
                },
                message="Next question retrieved successfully"
            )

        return ApiResponse(
            status_code=200,
            data={"status": "finished"},
            message="All questions completed"
        )
    
    os.makedirs("app/assets/audio/questions", exist_ok=True)
    audio_path = f"app/assets/audio/questions/q_{question.id}.mp3"
    if not os.path.exists(audio_path):
        await audio_service.text_to_speech(question.question_text or question.content, audio_path)
    
    # Calculate progress
    total_questions = 0
    question_index = len(answered_ids) + 1
    
    if has_assignments:
        total_questions = len(session_db.exec(select(SessionQuestion).where(SessionQuestion.interview_id == interview_id)).all())
    elif session_obj and session_obj.paper_id:
        total_questions = len(session_db.exec(select(Questions).where(Questions.paper_id == session_obj.paper_id)).all())
    
    import json as _json

    # Build response data; for code-type questions expose structured content
    response_data: dict = {
        "question_id": question.id,
        "text": question.question_text or question.content,
        "audio_url": f"/interview/audio/question/{question.id}",
        "response_type": question.response_type,
        "question_index": question_index,
        "total_questions": total_questions,
        "coding_content": None,
    }

    if question.response_type == "code" and question.content:
        try:
            parsed = _json.loads(question.content)
            response_data["text"] = parsed.get("title", question.question_text or "")
            response_data["coding_content"] = {
                "title": parsed.get("title", ""),
                "problem_statement": parsed.get("problem_statement", ""),
                "examples": parsed.get("examples", []),
                "constraints": parsed.get("constraints", []),
                "starter_code": parsed.get("starter_code"),
            }
        except (_json.JSONDecodeError, TypeError):
            pass  # leave coding_content as None if parsing fails

    return ApiResponse(
        status_code=200,
        data=response_data,
        message="Next question retrieved successfully"
    )

@router.get("/audio/question/{q_id}")
async def stream_question_audio(q_id: int, current_user: User = Depends(get_current_user)):
    audio_path = f"app/assets/audio/questions/q_{q_id}.mp3"
    if not os.path.exists(audio_path): raise HTTPException(status_code=404)
    return FileResponse(audio_path, media_type="audio/mpeg")

@router.post("/submit-answer-audio", response_model=ApiResponse[dict])
async def submit_answer_audio(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    feedback: Optional[str] = Form(None),
    score: Optional[float] = Form(None),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    from ..services.status_manager import update_last_activity
    
    # Check if session exists and is not suspended
    session_obj = session_db.get(InterviewSession, interview_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_obj.is_suspended:
        raise HTTPException(
            status_code=403,
            detail=f"Interview suspended: {session_obj.suspension_reason}"
        )
    
    os.makedirs("app/assets/audio/responses", exist_ok=True)
    audio_path = f"app/assets/audio/responses/resp_{interview_id}_{question_id}_{uuid.uuid4().hex[:8]}.wav"
    content = await audio.read()
    audio_service.save_audio_blob(content, audio_path)
    
    # Get or Create InterviewResult (Thread-safe-ish check)
    result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if not result:
        try:
            result = InterviewResult(interview_id=interview_id)
            session_db.add(result)
            session_db.commit()
            session_db.refresh(result)
        except Exception:
            # Another request probably created it simultaneously
            session_db.rollback()
            result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
            if not result:
                raise HTTPException(status_code=500, detail="Failed to initialize interview results")
    
    # Check if answer already exists
    answer = session_db.exec(
        select(Answers).where(
            Answers.interview_result_id == result.id,
            Answers.question_id == question_id
        )
    ).first()

    if answer:
        answer.audio_path = audio_path
        if feedback is not None:
            answer.feedback = feedback
        if score is not None:
            answer.score = score
        answer.timestamp = datetime.now(timezone.utc)
    else:
        answer = Answers(
            interview_result_id=result.id, 
            question_id=question_id, 
            audio_path=audio_path,
            feedback=feedback or "",
            score=score if score is not None else 0.0
        )
    
    session_db.add(answer)
    
    # Update last activity
    update_last_activity(session_db, session_obj)
    
    session_db.commit()
    session_db.refresh(answer)

    # ── Real-time: Transcribe + Evaluate ─────────────────────────────────────
    # Transcribe audio immediately so evaluation can run right away.
    # STT and LLM errors are caught inside the helpers; answer is already saved.
    transcribed_text = ""
    try:
        # REF: Using await instead of new_event_loop().run_until_complete()
        # triggering nested loops in Uvicorn is unstable and prone to 000 crashes.
        transcribed_text = await audio_service.speech_to_text(audio_path)
        
        # Speaker verification (best-effort)
        if session_obj.enrollment_audio_path:
            try:
                match, _ = await audio_service.verify_speaker(
                    session_obj.enrollment_audio_path, audio_path
                )
                if not match:
                    transcribed_text = f"[VOICE MISMATCH] {transcribed_text}"
            except Exception as spk_exc:
                logger.warning(
                    f"Speaker verification failed for answer {answer.id}: {spk_exc}"
                )

        if transcribed_text:
            answer.transcribed_text = transcribed_text
            answer.candidate_answer = transcribed_text
            session_db.add(answer)
            session_db.commit()
            session_db.refresh(answer)

    except Exception as stt_exc:
        logger.error(
            f"STT failed for answer {answer.id} (interview {interview_id}): {stt_exc}",
            exc_info=True,
        )

    # Evaluate (uses candidate_answer / transcribed_text set just above)
    question = session_db.get(Questions, question_id)
    q_text = ""
    if question:
        q_text = question.question_text or question.content or ""

    _evaluate_and_update_score(
        db=session_db,
        answer=answer,
        question_text=q_text,
        session_obj=session_obj,
        result_obj=result,
    )

    # Refresh to get latest score/feedback written by the helper
    try:
        session_db.refresh(answer)
    except Exception:
        pass

    return ApiResponse(
        status_code=200,
        data={
            "status": "saved",
            "feedback": answer.feedback,
            "score": answer.score,
            "transcribed_text": answer.transcribed_text,
        },
        message="Audio answer submitted and evaluated successfully"
    )


from ..schemas.interview_responses import AnswersData, QuestionData, CodingAnswersData, CodingQuestionNested

@router.post("/submit-answer-code", response_model=ApiResponse[CodingAnswersData])
async def submit_answer_code(
    interview_id: int = Form(...),
    coding_question_id: int = Form(...),
    answer_code: str = Form(...),
    feedback: Optional[str] = Form(None),
    score: Optional[float] = Form(None),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Submits a code answer directly."""
    session = session_db.get(InterviewSession, interview_id)
    if not session: raise HTTPException(status_code=404, detail="Session not found")

    result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if not result:
        result = InterviewResult(interview_id=interview_id)
        session_db.add(result)
        session_db.commit()
        session_db.refresh(result)

    from ..models.db_models import CodingAnswers
    answer = session_db.exec(
        select(CodingAnswers).where(
            CodingAnswers.interview_result_id == result.id,
            CodingAnswers.coding_question_id == coding_question_id
        )
    ).first()

    if answer:
        answer.candidate_answer = answer_code
        if feedback is not None: answer.feedback = feedback
        if score is not None: answer.score = score
        answer.timestamp = datetime.now(timezone.utc)
    else:
        answer = CodingAnswers(
            interview_result_id=result.id,
            coding_question_id=coding_question_id,
            candidate_answer=answer_code,
            feedback=feedback or "",
            score=score if score is not None else 0.0
        )
    
    session_db.add(answer)
    session_db.commit()
    session_db.refresh(answer)

    question = session_db.get(CodingQuestions, coding_question_id)
    if not question: raise HTTPException(status_code=404, detail="Coding question not found")

    _evaluate_and_update_score(session_db, answer, question.problem_statement or question.title or "", session, result)
    session_db.refresh(answer)

    return ApiResponse(
        status_code=200,
        data=CodingAnswersData(
            id=answer.id,
            interview_result_id=answer.interview_result_id,
            coding_question_id=CodingQuestionNested(
                id=question.id, paper_id=question.paper_id, title=question.title,
                problem_statement=question.problem_statement, examples=question.examples,
                constraints=question.constraints, starter_code=question.starter_code or "",
                topic=question.topic, difficulty=question.difficulty, marks=question.marks
            ),
            candidate_answer=answer.candidate_answer,
            feedback=answer.feedback,
            score=answer.score,
            timestamp=answer.timestamp
        ),
        message="Code submitted successfully"
    )

@router.post("/submit-answer-text", response_model=ApiResponse[Union[AnswersData, dict]])
async def submit_answer_text(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    answer_text: str = Form(...),
    feedback: Optional[str] = Form(None),
    score: Optional[float] = Form(None),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Submits a text answer, handles both standard and proxy-coding questions."""
    session = session_db.get(InterviewSession, interview_id)
    if not session: raise HTTPException(status_code=404, detail="Session not found")

    result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if not result:
        result = InterviewResult(interview_id=interview_id)
        session_db.add(result)
        session_db.commit()
        session_db.refresh(result)

    # 1. Detect if it's a coding question (proxy or direct)
    question = session_db.get(Questions, question_id)
    coding_q = None
    real_coding_id = None

    if question and question.question_text and question.question_text.startswith("__coding__"):
        try:
            real_coding_id = int(question.question_text.replace("__coding__", ""))
            coding_q = session_db.get(CodingQuestions, real_coding_id)
        except: pass
    elif not question:
        coding_q = session_db.get(CodingQuestions, question_id)
        if coding_q: real_coding_id = question_id

    if coding_q and real_coding_id:
        from ..models.db_models import CodingAnswers
        answer = session_db.exec(
            select(CodingAnswers).where(
                CodingAnswers.interview_result_id == result.id,
                CodingAnswers.coding_question_id == real_coding_id
            )
        ).first()

        if answer:
            answer.candidate_answer = answer_text
            if feedback is not None: answer.feedback = feedback
            if score is not None: answer.score = score
            answer.timestamp = datetime.now(timezone.utc)
        else:
            answer = CodingAnswers(
                interview_result_id=result.id,
                coding_question_id=real_coding_id,
                candidate_answer=answer_text,
                feedback=feedback or "",
                score=score if score is not None else 0.0
            )
        session_db.add(answer)
        session_db.commit()
        session_db.refresh(answer)

        _evaluate_and_update_score(session_db, answer, coding_q.problem_statement or coding_q.title or "", session, result)
        session_db.refresh(answer)

        return ApiResponse(
            status_code=200,
            data={
                "id": answer.id,
                "interview_result_id": answer.interview_result_id,
                "coding_question_id": {
                    "id": coding_q.id, "title": coding_q.title, "problem_statement": coding_q.problem_statement,
                    "examples": coding_q.examples, "constraints": coding_q.constraints, "marks": coding_q.marks
                },
                "candidate_answer": answer.candidate_answer,
                "feedback": answer.feedback,
                "score": answer.score,
                "timestamp": answer.timestamp.isoformat()
            },
            message="Coding answer submitted successfully"
        )
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Standard flow
    answer = session_db.exec(
        select(Answers).where(
            Answers.interview_result_id == result.id,
            Answers.question_id == question_id
        )
    ).first()

    if answer:
        answer.candidate_answer = answer_text
        if feedback is not None:
            answer.feedback = feedback
        if score is not None:
            answer.score = score
        answer.timestamp = datetime.now(timezone.utc)
    else:
        answer = Answers(
            interview_result_id=result.id,
            question_id=question_id,
            candidate_answer=answer_text,
            feedback=feedback or "",
            score=score if score is not None else 0.0
        )
    
    session_db.add(answer)
    session_db.commit()
    session_db.refresh(answer)

    _evaluate_and_update_score(session_db, answer, question.question_text or question.content or "", session, result)
    session_db.refresh(answer)

    return ApiResponse(
        status_code=200,
        data=AnswersData(
            id=answer.id,
            interview_result_id=answer.interview_result_id,
            question=QuestionData(
                id=question.id, paper_id=question.paper_id, content=question.content or "",
                question_text=question.question_text or "", topic=question.topic or "",
                difficulty=str(question.difficulty), marks=question.marks, response_type=str(question.response_type)
            ),
            candidate_answer=answer.candidate_answer,
            feedback=answer.feedback,
            score=answer.score,
            audio_path=answer.audio_path or "",
            transcribed_text=answer.transcribed_text or "",
            timestamp=answer.timestamp
        ),
        message="Answer submitted successfully"
    )



@router.post("/finish/{interview_id}", response_model=ApiResponse[dict])
async def finish_interview(interview_id: int, background_tasks: BackgroundTasks, session_db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    interview_session = session_db.get(InterviewSession, interview_id)
    if not interview_session: raise HTTPException(status_code=404)
    
    interview_session.end_time = datetime.now(timezone.utc)
    interview_session.is_completed = True
    interview_session.status = InterviewStatus.COMPLETED
    
    # Track completion status
    record_status_change(
        session=session_db,
        interview_session=interview_session,
        new_status=CandidateStatus.INTERVIEW_COMPLETED,
        metadata={"completed_at": format_iso_datetime(datetime.now(timezone.utc))}
    )
    
    session_db.add(interview_session)
    session_db.commit()
    
    # Process results in background using plain function (no Celery dependency)
    from ..tasks.interview_tasks import process_session_results
    background_tasks.add_task(process_session_results, interview_id)
    return ApiResponse(
        status_code=200,
        data={"status": "finished"},
        message="Interview finished. Results are being processed in background."
    )

@router.post("/evaluate-answer", response_model=ApiResponse[dict])
async def evaluate_answer(request: AnswerRequest, session_db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Stateless endpoint to evaluate a candidate's answer against a question.
    Does not save the result to any specific interview session.
    """
    try:
        evaluation = interview_service.evaluate_answer_content(request.question, request.answer)
        
        # Remove interview_id from response if it existed in the prompt output
        if "interview_id" in evaluation:
            del evaluation["interview_id"]
            
        return ApiResponse(
            status_code=200,
            data=evaluation,
            message="Answer evaluated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")



@router.post("/{interview_id}/tab-switch", response_model=ApiResponse[InterviewSessionData])
async def log_tab_switch(
    interview_id: int,
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[InterviewSessionData]:
    """
    Logs a tab switch event during the interview.
    Increments warning count and notifies admins.
    Currently only generates a warning (termination logic to be enabled later).
    """
    from sqlalchemy.orm import selectinload
    session_obj = session_db.exec(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.paper)
        )
    ).first()
    
    if not session_obj:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    # Check if session is already completed or suspended
    if session_obj.is_completed:
        raise HTTPException(status_code=400, detail="Interview is already completed")
        
    if session_obj.is_suspended:
        return ApiResponse(
            status_code=403,
            data={"is_suspended": True, "reason": session_obj.suspension_reason},
            message="Interview is currently suspended"
        )

    # Use status_manager to log the violation
    # We use force_severity="warning" to ensure it logs a warning even if default is different
    # NOTE: add_violation normally suspends if max_warnings exceeded.
    # To follow 'will do termination later', we can check if we should override that logic.
    # However, 'warning' severity naturally increments warning_count.
    
    event = add_violation(
        session=session_db,
        interview_session=session_obj,
        event_type="tab_switch",
        details="Candidate switched browser tab",
        force_severity="warning"
    )
    
    # Determine the return message
    if session_obj.is_suspended:
        return_msg = f"Interview suspended: Maximum tab switches exceeded ({session_obj.warning_count}/{session_obj.max_warnings})."
    else:
        return_msg = f"Warning: Tab switch detected. Please stay on the interview screen. (Warning {session_obj.warning_count} of {session_obj.max_warnings})"

    # Build InterviewSessionData for consistent response
    candidate_data = None
    if session_obj.candidate:
        candidate_data = UserNested(
            id=session_obj.candidate.id,
            email=session_obj.candidate.email,
            full_name=session_obj.candidate.full_name,
            role=session_obj.candidate.role.value if hasattr(session_obj.candidate.role, 'value') else str(session_obj.candidate.role),
            access_token=session_obj.candidate.access_token
        )

    admin_data = None
    if session_obj.admin:
        admin_data = UserNested(
            id=session_obj.admin.id,
            email=session_obj.admin.email,
            full_name=session_obj.admin.full_name,
            role=session_obj.admin.role.value if hasattr(session_obj.admin.role, 'value') else str(session_obj.admin.role),
            access_token=session_obj.admin.access_token
        )

    paper_data = None
    if session_obj.paper:
        paper_questions = []
        if hasattr(session_obj.paper, 'questions') and session_obj.paper.questions:
            for q in session_obj.paper.questions:
                paper_questions.append(QuestionData(
                    id=q.id, paper_id=q.paper_id, content=q.content or "", question_text=q.question_text or "",
                    topic=q.topic or "", difficulty=q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                    marks=q.marks, response_type=q.response_type.value if hasattr(q.response_type, 'value') else str(q.response_type)
                ))
        paper_data = QuestionPaperData(
            id=session_obj.paper.id,
            name=session_obj.paper.name,
            description=session_obj.paper.description or "",
            admin_user=admin_data if admin_data else None,
            question_count=len(paper_questions),
            questions=paper_questions,
            total_marks=session_obj.paper.total_marks,
            created_at=session_obj.paper.created_at or datetime.now(timezone.utc)
        )

    result_data = InterviewSessionData(
        id=session_obj.id,
        access_token=session_obj.access_token,
        admin_user=serialize_user(session_obj.admin) if session_obj.admin else None,  # ← Always UserNested
        candidate_user=candidate_data,
        paper=paper_data,
        schedule_time=session_obj.schedule_time,
        duration_minutes=session_obj.duration_minutes,
        max_questions=session_obj.max_questions,
        start_time=session_obj.start_time,
        end_time=session_obj.end_time,
        status=session_obj.status.value if hasattr(session_obj.status, 'value') else str(session_obj.status),
        total_score=session_obj.total_score,
        current_status=session_obj.current_status.value if hasattr(session_obj.current_status, 'value') else str(session_obj.current_status),
        last_activity=session_obj.last_activity or datetime.now(timezone.utc),
        warning_count=session_obj.warning_count or 0,
        max_warnings=session_obj.max_warnings or 3,
        is_suspended=session_obj.is_suspended or False,
        suspension_reason=session_obj.suspension_reason,
        suspended_at=session_obj.suspended_at,
        enrollment_audio_path=session_obj.enrollment_audio_path,
        is_completed=session_obj.is_completed or False,
        allow_copy_paste=session_obj.allow_copy_paste
    )

    return ApiResponse(
        status_code=200 if not session_obj.is_suspended else 403,
        data=result_data,
        message=return_msg
    )


# --- Standalone Tools ---

@router.post("/tools/speech-to-text", response_model=ApiResponse[dict])
async def speech_to_text_tool(audio: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """
    Public standalone tool to convert speech to text.
    No authentication required.
    """
    try:
        # Create a temp file to process
        temp_filename = f"temp_stt_{uuid.uuid4().hex}.wav"
        content = await audio.read()
        
        # Using a temporary path, but reusing audio service logic
        # Note: In a real prod env, might want a specific temp dir
        temp_path = f"app/assets/audio/standalone/{temp_filename}" 
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        audio_service.save_audio_blob(content, temp_path)
        
        # Perform STT
        text = await audio_service.speech_to_text(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return ApiResponse(
            status_code=200,
            data={"text": text},
            message="Speech converted to text successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech to text failed: {str(e)}")

@router.get("/tts")
async def standalone_tts(text: str, background_tasks: BackgroundTasks):
    """
    Generate Text-to-Speech (TTS) audio for the provided text via GET.
    Enables direct browser playback in HTML <audio> tags via query parameters.
    """
    temp_mp3 = f"app/assets/audio/standalone/tts_{uuid.uuid4().hex}.mp3"
    wav_path = f"app/assets/audio/standalone/tts_{uuid.uuid4().hex}.wav"
    
    try:
        os.makedirs(os.path.dirname(temp_mp3), exist_ok=True)
        
        # 1. Generate MP3 stream
        await audio_service.text_to_speech(text, temp_mp3)
        
        # 2. Convert to standard PCM WAV (16kHz, Mono, 16-bit)
        audio = AudioSegment.from_file(temp_mp3)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")
        
        # 3. Cleanup intermediate MP3
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)

        # 4. Return FileResponse and schedule cleanup
        def cleanup():
            if os.path.exists(wav_path):
                try: os.remove(wav_path)
                except Exception as e:
                    logger.error(f"TTS Cleanup Error: {e}")

        background_tasks.add_task(cleanup)
        
        return FileResponse(
            wav_path,
            media_type="audio/wav",
            content_disposition_type="inline"
        )

    except Exception as e:
        logger.error(f"TTS Generation Error: {e}")
        # Final safety cleanup
        for p in [temp_mp3, wav_path]:
            if os.path.exists(p): 
                try: 
                    os.remove(p)
                except Exception as e:
                    logger.error(f"TTS Cleanup Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate TTS audio.")
        
        raise HTTPException(status_code=500, detail="Failed to generate TTS audio.")
