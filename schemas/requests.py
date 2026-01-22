from typing import Optional
from pydantic import BaseModel

# Candidate Requests
class JoinRoomRequest(BaseModel):
    room_code: str
    password: str

class JoinRoomResponse(BaseModel):
    session_id: int
    room_code: str
    message: str

# Admin Requests
class RoomCreate(BaseModel):
    password: str
    max_sessions: Optional[int] = None

class RoomUpdate(BaseModel):
    password: Optional[str] = None
    max_sessions: Optional[int] = None
    is_active: Optional[bool] = None

# Interview Requests
class AnswerRequest(BaseModel):
    question: str
    answer: str

class EvaluateRequest(AnswerRequest):
    pass
