from typing import Optional
from pydantic import BaseModel
from models.db_models import UserRole

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

class UserLogin(BaseModel):
    email: str
    password: str

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

class ResumeQuestionRequest(BaseModel):
    context: Optional[str] = None
    resume_text: Optional[str] = None


