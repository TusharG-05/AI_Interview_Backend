from typing import Optional, List
from pydantic import BaseModel

# Candidate Responses
class HistoryItem(BaseModel):
    session_id: int
    paper_name: str
    date: str
    score: Optional[float] = None

class InterviewAccessResponse(BaseModel):
    session_id: int
    message: str # "START" or "WAIT"
    schedule_time: Optional[str] = None
    duration_minutes: Optional[int] = None

class PaperRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    question_count: int = 0
    created_at: str

class SessionRead(BaseModel):
    id: int
    candidate_name: str
    status: str
    scheduled_at: str
    score: float = None

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    email: str
    full_name: str
    expires_at: str

class InterviewLinkResponse(BaseModel):
    session_id: int
    access_token: str
    link: str
    scheduled_at: str
    warning: Optional[str] = None

class ProctoringLogItem(BaseModel):
    type: str
    time: str
    details: Optional[str] = None

class ResponseDetail(BaseModel):
    question: str
    answer: str
    score: str
    status: str # "Answered", "Skipped", "Pending AI"

class DetailedResult(BaseModel):
    session_id: int
    candidate: str
    date: str
    score: str
    flags: bool
    details: List[ResponseDetail]
    proctoring_logs: List[ProctoringLogItem]
