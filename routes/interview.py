"""Interview routes."""

import json
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from config.database import get_session
from models.db_models import Question, InterviewResponse, InterviewSession, User
from schemas.requests import AnswerRequest, EvaluateRequest
from auth.dependencies import get_current_user
from services import interview_service, resume_service

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter(prefix="/interview", tags=["Interview"])

@router.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main interview page"""
    return templates.TemplateResponse("interview.html", {"request": request})

@router.get("/general-questions")
async def get_general_questions(session: Session = Depends(get_session)):
    """Return the general coding questions from DB"""
    questions = session.exec(select(Question)).all()
    # Serialize for frontend
    return {"questions": [q.dict() for q in questions]}

@router.post("/evaluate-answer")
async def evaluate_answer(
    request: EvaluateRequest, 
    session_id: int, # Pass session_id from frontend query param or body
    session_db: Session = Depends(get_session)
):
    """Evaluate answer and store result in DB"""
    
    # Verify session
    interview_session = session_db.get(InterviewSession, session_id)
    if not interview_session:
        raise HTTPException(status_code=404, detail="Session not found")

    evaluation = interview_service.evaluate_answer_content(request.question, request.answer)
    
    # Logic update: We need question_id for the foreign key.
    # WORKAROUND: For this iteration, if we can't find the question, we create it.
    
    q_stmt = select(Question).where(Question.content == request.question)
    db_question = session_db.exec(q_stmt).first()
    
    if not db_question:
        # Create a dynamic question entry
        db_question = Question(content=request.question, topic="Dynamic/Resume", difficulty="Unknown")
        session_db.add(db_question)
        session_db.commit()
        session_db.refresh(db_question)

    new_response = InterviewResponse(
        session_id=session_id,
        question_id=db_question.id,
        answer_text=request.answer,
        evaluation_text=evaluation,
        score=0.0 # TODO: Parse score from evaluation text if possible
    )
    
    session_db.add(new_response)
    session_db.commit()
    
    return {"feedback": evaluation}

@router.post("/generate-resume-question")
async def generate_resume_question(
    context: str = Form(...),
    resume_text: str = Form(...)  # We'll expect the extracted text directly for simplicity in the flow
):
    """Generate a question based on resume and a random topic"""
    return interview_service.generate_resume_question_content(context, resume_text)

@router.post("/process-resume")
async def process_resume(resume: UploadFile = File(...)):
    """Extract text from PDF resume"""
    extracted_text = await resume_service.extract_text_from_pdf(resume)
    return {"text": extracted_text}

@router.post("/ask-custom-prompt")
async def ask_custom_prompt(request: dict):
    """Answer custom prompt from user"""
    prompt = request.get("prompt", "")
    response_content = interview_service.get_custom_response(prompt)
    return {"response": response_content}

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