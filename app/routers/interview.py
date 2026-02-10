from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Body
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import Questions, QuestionPaper, InterviewSession, InterviewResponse, SessionQuestion, InterviewStatus
from ..schemas.requests import AnswerRequest
from ..services import interview as interview_service
from ..services.audio import AudioService
from ..services.nlp import NLPService
from ..schemas.responses import InterviewAccessResponse
from pydantic import BaseModel
import os
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/interview", tags=["Interview"])
audio_service = AudioService()
nlp_service = NLPService()

class TTSRange(BaseModel):
    text: str




@router.get("/access/{token}", response_model=InterviewAccessResponse)
async def access_interview(token: str, session_db: Session = Depends(get_session)):
    """
    Validates the interview link and checks time constraints.
    """
    session = session_db.exec(select(InterviewSession).where(InterviewSession.access_token == token)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid Interview Link")
        
    now = datetime.utcnow()
    
    # 1. Status Check
    if session.status in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
        raise HTTPException(status_code=403, detail=f"Interview is {session.status.value}")
        
    # 2. Start Time Check
    if now < session.schedule_time:
        # Too early
        return InterviewAccessResponse(
            session_id=session.id,
            message="WAIT",
            schedule_time=session.schedule_time.isoformat(),
            duration_minutes=session.duration_minutes
        )
        
    # 3. Expiration Check
    expiration_time = session.schedule_time + timedelta(minutes=session.duration_minutes)
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
    return InterviewAccessResponse(
            session_id=session.id,
            message="START",
            schedule_time=session.schedule_time.isoformat(),
            duration_minutes=session.duration_minutes
    )


@router.post("/start-session/{session_id}")
async def start_session_logic(
    session_id: int,
    enrollment_audio: UploadFile = File(None),
    session_db: Session = Depends(get_session)
):
    """
    Called when candidate actually enters the interview session (uploads selfie/audio).
    Sets status to LIVE.
    """
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    session = session_db.get(InterviewSession, session_id)
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
        session.start_time = datetime.utcnow()
    
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
        
    return {"session_id": session.id, "status": "LIVE", "warning": warning}

@router.get("/next-question/{session_id}")
async def get_next_question(session_id: int, session_db: Session = Depends(get_session)):
    from ..services.status_manager import record_status_change, update_last_activity
    from ..models.db_models import CandidateStatus
    
    # Get session and check suspension
    session_obj = session_db.get(InterviewSession, session_id)
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
    answered_ids = [r.question_id for r in session_db.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()]
    
    # 2. Check if this session has assigned questions (Campaign mode)
    has_assignments = session_db.exec(
        select(SessionQuestion).where(SessionQuestion.session_id == session_id)
    ).first() is not None
    
    # Logic Update: If Bank is assigned, we should pull from Bank if no session_questions pre-assigned?
    # For now, sticking to logic:
    
    if has_assignments:
        # Campaign mode: Strictly follow assigned questions
        session_q = session_db.exec(
            select(SessionQuestion)
            .where(SessionQuestion.session_id == session_id)
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
    
    if not question: return {"status": "finished"}
    
    os.makedirs("app/assets/audio/questions", exist_ok=True)
    audio_path = f"app/assets/audio/questions/q_{question.id}.mp3"
    if not os.path.exists(audio_path):
        await audio_service.text_to_speech(question.question_text or question.content, audio_path)
    
    # Calculate progress
    total_questions = 0
    question_index = len(answered_ids) + 1
    
    if has_assignments:
        total_questions = len(session_db.exec(select(SessionQuestion).where(SessionQuestion.session_id == session_id)).all())
    elif session_obj and session_obj.paper_id:
        total_questions = len(session_db.exec(select(Questions).where(Questions.paper_id == session_obj.paper_id)).all())
    
    return {
        "question_id": question.id,
        "text": question.question_text or question.content,
        "audio_url": f"/interview/audio/question/{question.id}",
        "response_type": question.response_type,
        "question_index": question_index,
        "total_questions": total_questions
    }

@router.get("/audio/question/{q_id}")
async def stream_question_audio(q_id: int):
    audio_path = f"app/assets/audio/questions/q_{q_id}.mp3"
    if not os.path.exists(audio_path): raise HTTPException(status_code=404)
    return FileResponse(audio_path, media_type="audio/mpeg")

@router.post("/submit-answer")
async def submit_answer(
    session_id: int = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    session_db: Session = Depends(get_session)
):
    from ..services.status_manager import update_last_activity
    
    # Check if session exists and is not suspended
    session_obj = session_db.get(InterviewSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_obj.is_suspended:
        raise HTTPException(
            status_code=403,
            detail=f"Interview suspended: {session_obj.suspension_reason}"
        )
    
    os.makedirs("app/assets/audio/responses", exist_ok=True)
    audio_path = f"app/assets/audio/responses/resp_{session_id}_{question_id}_{uuid.uuid4().hex[:8]}.wav"
    content = await audio.read()
    audio_service.save_audio_blob(content, audio_path)
    
    response = InterviewResponse(session_id=session_id, question_id=question_id, audio_path=audio_path)
    session_db.add(response)
    
    # Update last activity
    update_last_activity(session_db, session_obj)
    
    session_db.commit()
    return {"status": "saved"}

@router.post("/finish/{session_id}")
async def finish_interview(session_id: int, background_tasks: BackgroundTasks, session_db: Session = Depends(get_session)):
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session: raise HTTPException(status_code=404)
    
    interview_session.end_time = datetime.utcnow()
    interview_session.is_completed = True
    interview_session.status = InterviewStatus.COMPLETED
    
    # Track completion status
    record_status_change(
        session=session_db,
        interview_session=interview_session,
        new_status=CandidateStatus.INTERVIEW_COMPLETED,
        metadata={"completed_at": datetime.utcnow().isoformat()}
    )
    
    session_db.add(interview_session)
    session_db.commit()
    
    background_tasks.add_task(process_session_results_unified, session_id)
    return {"status": "finished", "message": "Results are being processed by AI."}

# --- AI & Resume Specific ---

@router.post("/evaluate-answer")
async def evaluate_answer(request: AnswerRequest, session_id: int, session_db: Session = Depends(get_session)):
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session: raise HTTPException(status_code=404)

    try:
        evaluation = interview_service.evaluate_answer_content(request.question, request.answer)
        
        # This now only flushes, doesn't commit
        db_question = interview_service.get_or_create_question(session_db, request.question, topic="Dynamic")

        new_response = InterviewResponse(
            session_id=session_id,
            question_id=db_question.id,
            answer_text=request.answer,
            evaluation_text=evaluation["feedback"],
            score=evaluation["score"]
        )
        session_db.add(new_response)
        
        # ATOMIC COMMIT: Both Question (if new) and Response are saved together
        session_db.commit()
        return evaluation
    except Exception as e:
        session_db.rollback()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# --- Background Unified Processor ---

async def process_session_results_unified(session_id: int):
    from ..core.database import engine
    from ..core.logger import get_logger
    from sqlmodel import Session, select
    
    logger = get_logger(__name__)
    
    with Session(engine) as db:
        try:
            session = db.get(InterviewSession, session_id)
            if not session: 
                logger.warning(f"Session {session_id} not found for processing")
                return
            
            responses = db.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()
            for resp in responses:
                if resp.audio_path and not (resp.answer_text or resp.transcribed_text):
                    audio_service.cleanup_audio(resp.audio_path)
                    
                    # 1. Verification & Transcription (Async)
                    text = await audio_service.speech_to_text(resp.audio_path)
                    if session.enrollment_audio_path:
                        match, _ = audio_service.verify_speaker(session.enrollment_audio_path, resp.audio_path)
                        if not match: text = f"[VOICE MISMATCH] {text}"
                    
                    resp.answer_text = text
                    resp.transcribed_text = text # Compatibility
                    
                    # 2. LLM Evaluation
                    q_text = resp.question.question_text or resp.question.content or "General Question"
                    evaluation = interview_service.evaluate_answer_content(q_text, text)
                    
                    resp.evaluation_text = evaluation["feedback"]
                    resp.score = evaluation["score"]
                    db.add(resp)
                    db.commit()
            
            # Final Score Aggregation
            from ..utils import calculate_average_score
            all_scores = [r.score for r in responses if r.score is not None]
            session.total_score = calculate_average_score(all_scores)
            db.add(session)
            db.commit()
            logger.info(f"Session {session_id} processing completed successfully")
        except Exception as e:
            logger.error(f"Session {session_id} processing failed: {e}", exc_info=True)
            # Optionally: send notification to admin about processing failure

# --- Standalone Testing ---

@router.post("/tts")
async def standalone_tts(req: TTSRange):
    path = f"app/assets/audio/standalone/tts_{uuid.uuid4().hex[:8]}.mp3"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    await audio_service.text_to_speech(req.text, path)
    return FileResponse(path, media_type="audio/mpeg")
