"""Interview routes."""

import json
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from sqlmodel import Session, select
from config.database import get_session
from models.db_models import Question, InterviewResponse, InterviewSession, User
from schemas.requests import AnswerRequest, ResumeQuestionRequest
from auth.dependencies import get_current_user
from services import interview_service, resume_service
from services.audio import AudioService
import uuid
import os

audio_service = AudioService()


# Initialize templates
# Create router
router = APIRouter(prefix="/interview", tags=["Interview"])

@router.get("/general-questions")
async def get_general_questions(session: Session = Depends(get_session)):
    """Return the general coding questions from DB"""
    questions = session.exec(select(Question)).all()
    # Serialize for frontend
    return {"questions": [q.dict() for q in questions]}

@router.post("/evaluate-answer")
async def evaluate_answer(
    request: AnswerRequest, 
    session_id: int, # Pass session_id from frontend query param or body
    session_db: Session = Depends(get_session)
):
    """Evaluate answer and store result in DB"""
    
    # Verify session
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session:
        raise HTTPException(status_code=404, detail="Session not found")

    evaluation_result = interview_service.evaluate_answer_content(request.question, request.answer)
    follow_up = interview_service.generate_followup_question(request.question, request.answer)
    
    # Use helper to find or create question
    db_question = interview_service.get_or_create_question(
        session_db, 
        request.question, 
        topic="Dynamic/Resume"
    )

    new_response = InterviewResponse(
        session_id=session_id,
        question_id=db_question.id,
        answer_text=request.answer,
        evaluation_text=evaluation_result["feedback"],
        score=evaluation_result["score"]
    )
    
    session_db.add(new_response)
    session_db.commit()
    
    return {
        "feedback": evaluation_result["feedback"], 
        "score": evaluation_result["score"],
        "follow_up_question": follow_up
    }

@router.post("/submit-audio")
async def submit_audio(
    session_id: int = Form(...),
    question: str = Form(...),
    audio: UploadFile = File(...),
    session_db: Session = Depends(get_session)
):
    # 1. Save Audio
    os.makedirs("assets/audio/responses", exist_ok=True)
    audio_filename = f"resp_{session_id}_{uuid.uuid4().hex[:8]}.wav"
    audio_path = f"assets/audio/responses/{audio_filename}"
    
    content = await audio.read()
    audio_service.save_audio_blob(content, audio_path)
    
    # 2. Transcribe
    # Clean first?
    audio_service.cleanup_audio(audio_path)
    transcribed_text = audio_service.speech_to_text(audio_path)
    
    if not transcribed_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
    # 3. Evaluate (Reuse existing logic)
    # 3. Evaluate (Reuse existing logic)
    evaluation_result = interview_service.evaluate_answer_content(question, transcribed_text)
    follow_up = interview_service.generate_followup_question(question, transcribed_text)
    
    # 4. Save to DB using helper
    db_question = interview_service.get_or_create_question(
        session_db, 
        question, 
        topic="Audio/Dynamic"
    )

    new_response = InterviewResponse(
        session_id=session_id,
        question_id=db_question.id,
        answer_text=transcribed_text, # Store text
        evaluation_text=evaluation_result["feedback"],
        score=evaluation_result["score"]
    )
    
    session_db.add(new_response)
    session_db.commit()
    
    return {
        "transcription": transcribed_text,
        "feedback": evaluation_result["feedback"],
        "score": evaluation_result["score"],
        "follow_up_question": follow_up
    }


@router.post("/generate-resume-question")
async def generate_resume_question(
    request: ResumeQuestionRequest
):
    """Generate a question based on resume and a random topic"""
    # Ensure strings for the service
    context = request.context or ""
    resume_text = request.resume_text or ""
    return interview_service.generate_resume_question_content(context, resume_text)

@router.post("/process-resume")
async def process_resume(resume: UploadFile = File(...)):
    """Extract text from PDF resume"""
    extracted_text = await resume_service.extract_text_from_pdf(resume)
    return {"text": extracted_text}



@router.post("/finish")
async def finish_interview(
    session_id: int,
    session_db: Session = Depends(get_session)
):
    """Finish the interview session"""
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Calculate total score
    responses = session_db.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()
    total_score = sum([r.score for r in responses if r.score is not None])
    
    interview_session.end_time = datetime.utcnow()
    interview_session.total_score = total_score
    
    session_db.add(interview_session)
    session_db.commit()
    session_db.refresh(interview_session)
    
    return {"message": "Interview finished", "total_score": total_score}