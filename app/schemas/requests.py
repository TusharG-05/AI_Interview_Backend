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
class InterviewScheduleCreate(BaseModel):
    candidate_id: int
    bank_id: int
    schedule_time: str # ISO format expected from frontend
    duration_minutes: int = 180

# Removed: RoomCreate, BankCreate (handled in admin code), RoomUpdate

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
