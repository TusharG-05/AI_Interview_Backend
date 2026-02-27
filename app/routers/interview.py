from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Body
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User,Questions, QuestionPaper, InterviewSession, InterviewResult, Answers, SessionQuestion, InterviewStatus
from ..schemas.requests import AnswerRequest
from ..schemas.interview_result import UserNested, QuestionPaperNested
from ..services import interview as interview_service
from ..services.audio import AudioService
from ..schemas.responses import InterviewAccessResponse
from ..schemas.interview_result import UserNested, QuestionPaperNested
from ..schemas.interview_responses import InterviewSessionData, LoginUserNested, QuestionPaperData, QuestionData
from ..schemas.api_response import ApiResponse
from ..auth.dependencies import get_current_user
from pydantic import BaseModel
import os
import uuid
from datetime import datetime, timedelta, timezone

from pydub import AudioSegment
import logging

router = APIRouter(prefix="/interview", tags=["Interview"])
from ..utils import format_iso_datetime
from ..tasks.interview_tasks import process_session_results_task
logger = logging.getLogger(__name__)
audio_service = AudioService()

class TTSRange(BaseModel):
    text: str




@router.get("/access/{token}", response_model=ApiResponse[InterviewSessionData])
async def access_interview(
    token: str, 
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validates the interview link and checks time constraints.
    """
    from ..core.config import FRONTEND_URL
    from sqlalchemy.orm import selectinload

    session = session_db.exec(
        select(InterviewSession)
        .where(InterviewSession.access_token == token)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.paper)
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Invalid Interview Link")
        
    # Build nested objects from preloaded relationships
    candidate_data = None
    if session.candidate:
        candidate_data = LoginUserNested(
            id=str(session.candidate.id),
            email=session.candidate.email,
            full_name=session.candidate.full_name,
            role=session.candidate.role.value if hasattr(session.candidate.role, 'value') else str(session.candidate.role),
            access_token=session.candidate.access_token
        )

    admin_data = None
    if session.admin:
        admin_data = LoginUserNested(
            id=str(session.admin.id),
            email=session.admin.email,
            full_name=session.admin.full_name,
            role=session.admin.role.value if hasattr(session.admin.role, 'value') else str(session.admin.role),
            access_token=session.admin.access_token
        )

    paper_data = None
    if session.paper:
        # For the access endpoint, questions list is expected and adminUser is a string per user request layout, 
        # but to keep it safe as LoginUserNested like the schema expects. If its None, we handle it.
        # Note: The query doesn't selectinload questions initially in this endpoint (lines 43-48). We must ensure it's loaded if accessed.
        # But `session.paper.questions` might still lazy load. 
        paper_questions = []
        if hasattr(session.paper, 'questions') and session.paper.questions:
            for q in session.paper.questions:
                paper_questions.append(QuestionData(
                    id=q.id, paper_id=q.paper_id, content=q.content or "", question_text=q.question_text or "",
                    topic=q.topic or "", difficulty=q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                    marks=q.marks, response_type=q.response_type.value if hasattr(q.response_type, 'value') else str(q.response_type)
                ))
                
        paper_data = QuestionPaperData(
            id=session.paper.id,
            name=session.paper.name,
            description=session.paper.description or "",
            adminUser=admin_data if admin_data else 0, # Map to admin_data if exists per request schema
            question_count=len(paper_questions),
            questions=paper_questions,
            total_marks=session.paper.total_marks,
            created_at=session.paper.created_at or datetime.now(timezone.utc)
        )

    invite_link = f"{FRONTEND_URL}/interview/{session.access_token}"
        
    now = datetime.now(timezone.utc)
    
    # 1. Status Check
    if session.status in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
        raise HTTPException(status_code=403, detail=f"Interview is {session.status.value}")
        
    # 2. Start Time Check
    schedule_time = session.schedule_time
    if schedule_time.tzinfo is None:
        schedule_time = schedule_time.replace(tzinfo=timezone.utc)
        
    if now < schedule_time:
        # Too early
        access_data = InterviewSessionData(
            id=session.id,
            access_token=session.access_token,
            admin_id=admin_data,
            candidate_id=candidate_data,
            paper_id=paper_data,
            schedule_time=session.schedule_time,
            duration_minutes=session.duration_minutes,
            max_questions=session.max_questions,
            start_time=session.start_time,
            end_time=session.end_time,
            status=session.status.value if hasattr(session.status, 'value') else str(session.status),
            total_score=session.total_score,
            current_status="WAIT", # Special front-end flag preserved from old behavior, technically outside enum but supported dynamically
            last_activity=session.last_activity or now,
            warning_count=session.warning_count or 0,
            max_warnings=session.max_warnings or 3,
            is_suspended=session.is_suspended or False,
            suspension_reason=session.suspension_reason,
            suspended_at=session.suspended_at,
            enrollment_audio_path=session.enrollment_audio_path,
            is_completed=session.is_completed or False
        )
        return ApiResponse(
            status_code=200,
            data=access_data,
            message="Interview not yet started. Please wait."
        )
        
    # 3. Expiration Check
    expiration_time = schedule_time + timedelta(minutes=session.duration_minutes)
    if now > expiration_time:
         session.status = InterviewStatus.EXPIRED
         session_db.add(session)
         session_db.commit()
         raise HTTPException(status_code=403, detail="Interview link has expired")
         
    # 4. Track link access
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    # Only record if not already accessed
    if session.current_status == CandidateStatus.INVITED:
        record_status_change(
            session=session_db,
            interview_session=session,
            new_status=CandidateStatus.LINK_ACCESSED
        )
    
    # 6. Build the final standard response format
    result_data = InterviewSessionData(
        id=session.id,
        access_token=session.access_token,
        admin_id=admin_data,
        candidate_id=candidate_data,
        paper_id=paper_data,
        schedule_time=session.schedule_time,
        duration_minutes=session.duration_minutes,
        max_questions=session.max_questions,
        start_time=session.start_time,
        end_time=session.end_time,
        status=session.status.value if hasattr(session.status, 'value') else str(session.status),
        total_score=session.total_score,
        current_status=session.current_status.value if hasattr(session.current_status, 'value') else str(session.current_status),
        last_activity=session.last_activity or now,
        warning_count=session.warning_count or 0,
        max_warnings=session.max_warnings or 3,
        is_suspended=session.is_suspended or False,
        suspension_reason=session.suspension_reason,
        suspended_at=session.suspended_at,
        enrollment_audio_path=session.enrollment_audio_path,
        is_completed=session.is_completed or False
    )

    return ApiResponse(
        status_code=200,
        data=result_data,
        message="Access Granted"
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
            audio_service.cleanup_audio(enrollment_path)
            
            # Silence/Quality Check
            if audio_service.calculate_energy(enrollment_path) < 50:
                 warning = "Enrolled audio is very quiet. Speaker verification might be inaccurate."
            
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
        embeddings_map = {}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            try:
                arc_objs = DeepFace.represent(img_path=tmp_path, model_name="ArcFace", enforce_detection=False)
                if arc_objs:
                    embeddings_map["ArcFace"] = arc_objs[0]["embedding"]
            except Exception as e:
                _logger.warning(f"ArcFace embedding failed: {e}")

            try:
                sface_objs = DeepFace.represent(img_path=tmp_path, model_name="SFace", enforce_detection=False)
                if sface_objs:
                    embeddings_map["SFace"] = sface_objs[0]["embedding"]
            except Exception as e:
                _logger.warning(f"SFace embedding failed: {e}")

            if embeddings_map:
                candidate.face_embedding = json.dumps(embeddings_map)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        _logger.error(f"Embedding generation failed (non-fatal): {e}")

    # 5. Store image as base64 in database profile_image instead of local disk
    import base64
    base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
    candidate.profile_image = f"data:{file.content_type};base64,{base64_encoded}"
    
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
            "candidate_id": candidate.id
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
    
    return ApiResponse(
        status_code=200,
        data={
            "question_id": question.id,
            "text": question.question_text or question.content,
            "audio_url": f"/interview/audio/question/{question.id}",
            "response_type": question.response_type,
            "question_index": question_index,
            "total_questions": total_questions
        },
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
    
    # Save Answer
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
    return ApiResponse(
        status_code=200,
        data={
            "status": "saved",
            "feedback": answer.feedback,
            "score": answer.score
        },
        message="Audio answer submitted successfully"
    )

from ..schemas.interview_responses import AnswersData, QuestionData

@router.post("/submit-answer-text", response_model=ApiResponse[AnswersData])
async def submit_answer_text(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    answer_text: str = Form(...),
    feedback: Optional[str] = Form(None),
    score: Optional[float] = Form(None),
    session_db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a text answer for a question.
    Saves the response. If feedback and score are provided (pre-evaluated),
    background processing will skip redundant evaluation.
    """
    # Verify session exists
    session = session_db.get(InterviewSession, interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get or Create InterviewResult
    result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if not result:
        try:
            result = InterviewResult(interview_id=interview_id)
            session_db.add(result)
            session_db.commit()
            session_db.refresh(result)
        except Exception:
            session_db.rollback()
            result = session_db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
            if not result:
                raise HTTPException(status_code=500, detail="Failed to initialize interview results")

    answer = Answers(
        interview_result_id=result.id,
        question_id=question_id,
        candidate_answer=answer_text,
        feedback=feedback or "",
        score=score if score is not None else 0.0
    )
    session_db.add(answer)
    session_db.commit()
    
    # Load the related question
    question = session_db.get(Questions, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    question_data = QuestionData(
        id=question.id,
        paper_id=question.paper_id,
        content=question.content or "",
        question_text=question.question_text or "",
        topic=question.topic or "",
        difficulty=question.difficulty.value if hasattr(question.difficulty, 'value') else str(question.difficulty),
        marks=question.marks,
        response_type=question.response_type.value if hasattr(question.response_type, 'value') else str(question.response_type)
    )
    
    answer_data = AnswersData(
        id=answer.id,
        interview_result_id=answer.interview_result_id,
        Question_id=question_data,
        candidate_answer=answer.candidate_answer,
        feedback=answer.feedback,
        score=answer.score,
        audio_path=answer.audio_path,
        transcribed_text=answer.transcribed_text,
        timestamp=answer.timestamp
    )
    
    # Return the exact requested schema
    return ApiResponse(
        status_code=200,
        data=answer_data,
        message="Text answer submitted successfully"
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


# --- Background Unified Processor ---

# --- Legacy Processor Removed (Migrated to Celery) ---




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
