from typing import Optional
from pydantic import BaseModel

# Candidate Responses
class HistoryItem(BaseModel):
    session_id: int
    room_code: str
    date: str
    score: float = None

# Admin Responses
class RoomRead(BaseModel):
    id: int
    room_code: str
    password: str
    is_active: bool
    max_sessions: Optional[int]
    active_sessions_count: int = 0

class SessionRead(BaseModel):
    id: int
    candidate_name: str
    room_code: str
    start_time: str
    total_score: float = None

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

class JoinRoomResponse(BaseModel):
    session_id: int
    room_code: str
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

