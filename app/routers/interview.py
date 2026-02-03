from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import Question, InterviewSession, InterviewResponse, SessionQuestion
from ..schemas.requests import AnswerRequest
from ..services import interview as interview_service, resume as resume_service
from ..services.audio import AudioService
from ..services.nlp import NLPService
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/interview", tags=["Interview"])
audio_service = AudioService()
nlp_service = NLPService()

class TTSRange(BaseModel):
    text: str

class EvaluateRequest(BaseModel):
    candidate_text: str
    reference_text: str

@router.get("/general-questions")
async def get_general_questions(session: Session = Depends(get_session)):
    questions = session.exec(select(Question)).all()
    return {"questions": [q.dict() for q in questions]}

@router.post("/start")
async def start_interview(
    candidate_name: str = Form("Candidate"), 
    enrollment_audio: UploadFile = File(None),
    session_db: Session = Depends(get_session)
):
    new_session = InterviewSession(candidate_name=candidate_name, start_time=datetime.utcnow())
    session_db.add(new_session)
    session_db.commit()
    session_db.refresh(new_session)
    
    warning = None
    if enrollment_audio:
        os.makedirs("app/assets/audio/enrollment", exist_ok=True)
        enrollment_path = f"app/assets/audio/enrollment/enroll_{new_session.id}.wav"
        content = await enrollment_audio.read()
        audio_service.save_audio_blob(content, enrollment_path)
        audio_service.cleanup_audio(enrollment_path)
        
        # Silence/Quality Check
        if audio_service.calculate_energy(enrollment_path) < 50:
             warning = "Enrolled audio is very quiet. Speaker verification might be inaccurate."
        
        new_session.enrollment_audio_path = enrollment_path
        session_db.add(new_session)
        session_db.commit()
        
    return {"session_id": new_session.id, "warning": warning}

@router.get("/next-question/{session_id}")
async def get_next_question(session_id: int, session_db: Session = Depends(get_session)):
    # 1. Get answered questions
    answered_ids = [r.question_id for r in session_db.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()]
    
    # 2. Check if this session has assigned questions (Campaign mode)
    has_assignments = session_db.exec(
        select(SessionQuestion).where(SessionQuestion.session_id == session_id)
    ).first() is not None
    
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
        # Legacy mode: Use general pool
        question = session_db.exec(select(Question).where(~Question.id.in_(answered_ids))).first()
    
    if not question: return {"status": "finished"}
    
    os.makedirs("app/assets/audio/questions", exist_ok=True)
    audio_path = f"app/assets/audio/questions/q_{question.id}.mp3"
    if not os.path.exists(audio_path):
        await audio_service.text_to_speech(question.question_text or question.content, audio_path)
    
    return {
        "question_id": question.id,
        "text": question.question_text or question.content,
        "audio_url": f"/interview/audio/question/{question.id}"
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
    os.makedirs("app/assets/audio/responses", exist_ok=True)
    audio_path = f"app/assets/audio/responses/resp_{session_id}_{question_id}_{uuid.uuid4().hex[:8]}.wav"
    content = await audio.read()
    audio_service.save_audio_blob(content, audio_path)
    
    response = InterviewResponse(session_id=session_id, question_id=question_id, audio_path=audio_path)
    session_db.add(response)
    session_db.commit()
    return {"status": "saved"}

@router.post("/finish/{session_id}")
async def finish_interview(session_id: int, background_tasks: BackgroundTasks, session_db: Session = Depends(get_session)):
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session: raise HTTPException(status_code=404)
    
    interview_session.end_time = datetime.utcnow()
    interview_session.is_completed = True
    session_db.add(interview_session)
    session_db.commit()
    
    background_tasks.add_task(process_session_results_unified, session_id)
    return {"status": "finished", "message": "Results are being processed by AI."}

# --- AI & Resume Specific ---

@router.post("/evaluate-answer")
async def evaluate_answer(request: AnswerRequest, session_id: int, session_db: Session = Depends(get_session)):
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session: raise HTTPException(status_code=404)

    evaluation = interview_service.evaluate_answer_content(request.question, request.answer)
    db_question = interview_service.get_or_create_question(session_db, request.question, topic="Dynamic")

    new_response = InterviewResponse(
        session_id=session_id,
        question_id=db_question.id,
        answer_text=request.answer,
        evaluation_text=evaluation["feedback"],
        score=evaluation["score"]
    )
    session_db.add(new_response)
    session_db.commit()
    return evaluation

from ..auth.dependencies import get_current_user
from ..models.db_models import User

@router.post("/generate-resume-question")
async def generate_resume_question(
    context: str = Form(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    if not current_user.resume_text:
        raise HTTPException(status_code=400, detail="No resume found. Please upload a resume first.")
        
    return interview_service.generate_resume_question_content(context, current_user.resume_text)

@router.post("/process-resume")
async def process_resume(
    resume: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    text = await resume_service.extract_text_from_pdf(resume)
    if not text:
         raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
    
    # Persist to User Profile
    current_user.resume_text = text
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Resume processed and saved successfully.", "preview": text[:100] + "..."}

# --- Background Unified Processor ---

def process_session_results_unified(session_id: int):
    from ..core.database import engine
    from sqlmodel import Session, select
    with Session(engine) as db:
        try:
            session = db.get(InterviewSession, session_id)
            if not session: return
            
            responses = db.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()
            for resp in responses:
                if resp.audio_path and not (resp.answer_text or resp.transcribed_text):
                    audio_service.cleanup_audio(resp.audio_path)
                    
                    # 1. Verification & Transcription
                    text = audio_service.speech_to_text(resp.audio_path)
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
            all_scores = [r.score for r in responses if r.score is not None]
            session.total_score = sum(all_scores) / len(all_scores) if all_scores else 0
            db.add(session)
            db.commit()
            print(f"DEBUG: Session {session_id} Unified Processing Complete.")
        except Exception as e:
            print(f"ERROR: Session {session_id} Processing Failed: {e}")

# --- Standalone Testing ---

@router.post("/tts")
async def standalone_tts(req: TTSRange):
    path = f"app/assets/audio/standalone/tts_{uuid.uuid4().hex[:8]}.mp3"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    await audio_service.text_to_speech(req.text, path)
    return FileResponse(path, media_type="audio/mpeg")

@router.post("/evaluate")
async def standalone_evaluate(req: EvaluateRequest):
    return interview_service.evaluate_answer_content(req.reference_text, req.candidate_text)
