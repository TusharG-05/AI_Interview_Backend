"""Interview routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.requests import QuestionRequest, AnswerRequest, CustomPromptRequest
from config.settings import local_llm
from prompts.interview import interview_prompt
from prompts.evaluation import evaluation_prompt

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()

# Create the Chains
interview_chain = interview_prompt | local_llm
evaluation_chain = evaluation_prompt | local_llm


@router.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main interview page"""
    return templates.TemplateResponse("interview.html", {"request": request})


@router.post("/ask-question")
async def get_question(request: QuestionRequest):
    """Generate a technical interview question"""
    response = interview_chain.invoke({
        "context": request.context,
        "topic": request.topic
    })
    return {"question": response.content}


@router.post("/evaluate-answer")
async def evaluate_answer(request: AnswerRequest):
    """Evaluate the candidate's answer and provide feedback"""
    response = evaluation_chain.invoke({
        "question": request.question,
        "answer": request.answer
    })
    return {"feedback": response.content}


@router.post("/ask-custom-prompt")
async def ask_custom_prompt(request: CustomPromptRequest):
    """Answer custom prompt from user"""
    response = local_llm.invoke(request.prompt)
    return {"response": response.content}
