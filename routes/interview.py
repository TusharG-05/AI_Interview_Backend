"""Interview routes."""

import fitz  # PyMuPDF
import json
import random
import os
from typing import Optional, List, Dict
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from config.settings import local_llm
from prompts.interview import interview_prompt
from prompts.evaluation import evaluation_prompt
from models.requests import AnswerRequest, EvaluateRequest

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()

# Create the Chains
interview_chain = interview_prompt | local_llm
evaluation_chain = evaluation_prompt | local_llm

# Constants
QUESTIONS_FILE = "config/questions.json"
RESULTS_FILE = "results.json"
RESUME_TOPICS = ["Data Structures & Algorithms", "System Design", "Database Management", "API Design", "Security", "Scalability", "DevOps"]

def load_general_questions():
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_result(result: Dict):
    results = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r') as f:
                results = json.load(f)
        except json.JSONDecodeError:
            pass
    
    results.append(result)
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=4)

@router.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main interview page"""
    return templates.TemplateResponse("interview.html", {"request": request})

@router.get("/general-questions")
async def get_general_questions():
    """Return the static general coding questions"""
    return {"questions": load_general_questions()}

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