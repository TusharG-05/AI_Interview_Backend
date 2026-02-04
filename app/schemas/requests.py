from typing import Optional
from pydantic import BaseModel
from ..models.db_models import UserRole

# Candidate Requests


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None

class AdminCreate(BaseModel):
    email: str
    password: str
    full_name: str


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CANDIDATE

# Admin Requests
class InterviewScheduleCreate(BaseModel):
    candidate_id: int
    paper_id: int
    schedule_time: str # ISO format expected from frontend
    duration_minutes: int = 180



# Interview Requests
class AnswerRequest(BaseModel):
    question: str
    answer: str

class PaperUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class QuestionUpdate(BaseModel):
    content: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str
class QuestionCreate(BaseModel):
    content: str
    topic: Optional[str] = "General"
    difficulty: str = "Medium"
    marks: int = 1
