from typing import Optional
from pydantic import BaseModel, Field
from ..models.db_models import UserRole, InterviewRound



# Candidate Requests
class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None  # String, will be converted to UserRole
    resume_text: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CANDIDATE

# Admin Requests
class InterviewScheduleCreate(BaseModel):
    candidate_id: int
    paper_id: int
    team_id: int  # Required: must assign interview to a team
    interview_round: InterviewRound  # Required: e.g. ROUND_1, ROUND_2
    schedule_time: str # ISO format expected from frontend
    duration_minutes: int = 1440
    max_questions: Optional[int] = None  # Limit questions, None = use all
    allow_copy_paste: bool = False  # Whether candidate can copy/paste during interview

# Team Requests (super admin only for create/update/delete)
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class InterviewUpdate(BaseModel):
    schedule_time: Optional[str] = None  # ISO format
    duration_minutes: Optional[int] = None
    status: Optional[str] = None  # 'scheduled', 'cancelled', etc.
    paper_id: Optional[int] = None  # Allow changing question paper
    max_questions: Optional[int] = None  # Update question limit
    allow_copy_paste: Optional[bool] = None  # Update copy/paste permission

class ResponseUpdate(BaseModel):
    """Update individual response within a result"""
    response_id: int
    score: Optional[float] = None
    evaluation_text: Optional[str] = None

class ResultUpdate(BaseModel):
    """Update overall result and individual responses"""
    total_score: Optional[float] = None
    responses: Optional[list] = None  # List of ResponseUpdate dicts

# Interview Requests
class AnswerRequest(BaseModel):
    question: str
    answer: str

class PaperUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class QuestionUpdate(BaseModel):
    content: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None
    response_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    access_token: Optional[str] = None    
class QuestionCreate(BaseModel):
    content: str
    topic: Optional[str] = "General"
    difficulty: str = "Medium"
    marks: int = 1
    response_type: str = "audio"


class GeneratePaperRequest(BaseModel):
    ai_prompt: str = Field(..., min_length=5, description="Topic or job description to base questions on")
    years_of_experience: int = Field(..., ge=0, le=40, description="Candidate's expected years of experience")
    num_questions: int = Field(..., ge=1, le=50, description="Number of questions to generate")
    paper_name: Optional[str] = Field(None, description="Optional name for the question paper")
