from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Body
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import Questions, QuestionPaper, InterviewSession, InterviewResult, Answers, SessionQuestion, InterviewStatus
from ..schemas.requests import AnswerRequest
from ..services import interview as interview_service
from ..services.audio import AudioService
from ..services.nlp import NLPService
from ..schemas.responses import InterviewAccessResponse
from ..schemas.api_response import ApiResponse
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




@router.get("/access/{token}", response_model=ApiResponse[InterviewAccessResponse])
async def access_interview(token: str, session_db: Session = Depends(get_session)):
    """
    Validates the interview link and checks time constraints.
    """
    session = session_db.exec(select(InterviewSession).where(InterviewSession.access_token == token)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid Interview Link")
        
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
        access_data = InterviewAccessResponse(
            interview_id=session.id,
            candidate_id=session.candidate_id,
            admin_id=session.admin_id,
            paper_id=session.paper_id,
            message="WAIT",
            schedule_time=format_iso_datetime(session.schedule_time),
            duration_minutes=session.duration_minutes,
            status=session.status.value,
            max_questions=session.max_questions
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
    
    # 5. Success - Allow Entry
    access_data = InterviewAccessResponse(
        interview_id=session.id,
        candidate_id=session.candidate_id,
        admin_id=session.admin_id,
        paper_id=session.paper_id,
        message="START",
        schedule_time=format_iso_datetime(session.schedule_time),
        duration_minutes=session.duration_minutes,
        status=session.status.value,
        max_questions=session.max_questions
    )
    return ApiResponse(
        status_code=200,
        data=access_data,
        message="Interview access granted"
    )


@router.post("/start-session/{interview_id}", response_model=ApiResponse[dict])
async def start_session_logic(
    interview_id: int,
    enrollment_audio: UploadFile = File(None),
    session_db: Session = Depends(get_session)
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
            session_db.add(session)
            
            # Track enrollment completion
            record_status_change(
                session=session_db,
                interview_session=session,
                new_status=CandidateStatus.ENROLLMENT_COMPLETED
            )
            
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
    session_db: Session = Depends(get_session)
):
    """
    Allows candidate to upload their reference selfie via interview session context.
    Does NOT require JWT authentication.
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

    # 5. Save to disk
    upload_dir = "app/assets/images/profiles"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/user_{candidate.id}.jpg"
    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)
    
    candidate.profile_image = file_path
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
async def get_next_question(interview_id: int, session_db: Session = Depends(get_session)):
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
        session_q = session_db.exec(
            select(SessionQuestion)
            .where(SessionQuestion.interview_id == interview_id)
            .where(~SessionQuestion.question_id.in_(answered_ids))
            .order_by(SessionQuestion.sort_order)
        ).first()
        question = session_q.question if session_q else None
    else:
        # Fallback: Pull from the assigned Paper (if any) or General pool
        if session_obj and session_obj.paper_id:
             # Security Fix: Strictly scope to the assigned paper
             question = session_db.exec(
                 select(Questions)
                 .where(Questions.paper_id == session_obj.paper_id)
                 .where(~Questions.id.in_(answered_ids))
             ).first()
        else:
             # Pull only from global/orphaned pool, never from other papers
             question = session_db.exec(
                 select(Questions)
                 .where(Questions.paper_id == None)
                 .where(~Questions.id.in_(answered_ids))
             ).first()
    
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
async def stream_question_audio(q_id: int):
    audio_path = f"app/assets/audio/questions/q_{q_id}.mp3"
    if not os.path.exists(audio_path): raise HTTPException(status_code=404)
    return FileResponse(audio_path, media_type="audio/mpeg")

@router.post("/submit-answer-audio", response_model=ApiResponse[dict])
async def submit_answer_audio(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    session_db: Session = Depends(get_session)
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
        audio_path=audio_path
    )
    session_db.add(answer)
    
    # Update last activity
    update_last_activity(session_db, session_obj)
    
    session_db.commit()
    return ApiResponse(
        status_code=200,
        data={"status": "saved"},
        message="Audio answer submitted successfully"
    )

@router.post("/submit-answer-text", response_model=ApiResponse[dict])
async def submit_answer_text(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    answer_text: str = Form(...),
    session_db: Session = Depends(get_session)
):
    """
    Submits a text answer for a question.
    Saves the response but delays evaluation until the interview finishes.
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
        candidate_answer=answer_text
    )
    session_db.add(answer)
    session_db.commit()
    return ApiResponse(
        status_code=200,
        data={"status": "saved"},
        message="Text answer submitted successfully"
    )


@router.post("/finish/{interview_id}", response_model=ApiResponse[dict])
async def finish_interview(interview_id: int, background_tasks: BackgroundTasks, session_db: Session = Depends(get_session)):
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
async def evaluate_answer(request: AnswerRequest, session_db: Session = Depends(get_session)):
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
async def speech_to_text_tool(audio: UploadFile = File(...)):
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
