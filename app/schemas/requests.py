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
    max_sessions: Optional[int] = 30


class RoomUpdate(BaseModel):
    password: Optional[str] = None
    max_sessions: Optional[int] = None
    is_active: Optional[bool] = None

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
