from typing import Optional
from pydantic import BaseModel
from ..models.db_models import UserRole

# Candidate Requests
class JoinRoomRequest(BaseModel):
    room_code: str
    password: str

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
class RoomCreate(BaseModel):
    password: str
    bank_id: int
    question_count: int = 5
    max_sessions: Optional[int] = 30
    interviewer_id: Optional[int] = None

class BankCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoomUpdate(BaseModel):
    password: Optional[str] = None
    max_sessions: Optional[int] = None
    is_active: Optional[bool] = None
    interviewer_id: Optional[int] = None

# Interview Requests
class AnswerRequest(BaseModel):
    question: str
    answer: str


class LoginRequest(BaseModel):
    email: str
    password: str
class QuestionCreate(BaseModel):
    content: str
    topic: Optional[str] = "General"
    difficulty: str = "Medium"
    reference_answer: Optional[str] = None
    marks: int = 1
