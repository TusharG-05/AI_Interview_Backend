"""Interview routes."""

import fitz 
import json
import random
import os
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from config.settings import local_llm
from config.database import get_session
from models.db_models import Question, InterviewResponse, InterviewSession
from prompts.interview import interview_prompt
from prompts.evaluation import evaluation_prompt
from models.requests import AnswerRequest, EvaluateRequest
from auth.dependencies import get_current_user
from models.db_models import User

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()

# Create the Chains
interview_chain = interview_prompt | local_llm
evaluation_chain = evaluation_prompt | local_llm

# Constants
RESUME_TOPICS = ["Data Structures & Algorithms", "System Design", "Database Management", "API Design", "Security", "Scalability", "DevOps"]

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

    response = evaluation_chain.invoke({
        "question": request.question,
        "answer": request.answer
    })
    
    evaluation = response.content
    
    # Find question ID if possible, or create a 'Dynamic' question?
    # For now, let's try to match question content or just store 0 if it's dynamic/resume
    # Ideally frontend sends question_id.
    # We will assume request has question_id if it's a DB question.
    # For now, let's just create a new Response.
    
    # Logic update: We need question_id for the foreign key.
    # If it's a resume question, we might need a "Dynamic Question" table or allow null question_id (but it is defined as int).
    # Let's check `models/db_models.py` -> question_id is int foreign key.
    # If it's a generated question, we should probably save it to the Question table first or have a 'Custom' type.
    
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
    
    # Pick a random topic
    random_topic = random.choice(RESUME_TOPICS)
    
    full_context = f"User Provided Context: {context}\n\nResume Content: {resume_text}"

    response = interview_chain.invoke({
        "context": full_context,
        "topic": random_topic
    })
    
    return {
        "question": response.content,
        "topic": random_topic
    }

@router.post("/process-resume")
async def process_resume(resume: UploadFile = File(...)):
    """Extract text from PDF resume"""
    extracted_text = ""
    if resume.filename.endswith('.pdf'):
        pdf_content = await resume.read()
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page in doc:
                extracted_text += page.get_text()
    
    return {"text": extracted_text}

@router.post("/evaluate-answer")
async def evaluate_answer(request: EvaluateRequest):
    """Evaluate answer and store result"""
    response = evaluation_chain.invoke({
        "question": request.question,
        "answer": request.answer
    })
    
    evaluation = response.content
    
    # Save the result
    save_result({
        "question": request.question,
        "answer": request.answer,
        "evaluation": evaluation
    })
    
    return {"feedback": evaluation}

@router.post("/ask-custom-prompt")
async def ask_custom_prompt(request: dict):
    """Answer custom prompt from user"""
    prompt = request.get("prompt", "")
    response = local_llm.invoke(prompt)
    return {"response": response.content}