from typing import Optional, List
from pydantic import BaseModel

# Candidate Responses
class HistoryItem(BaseModel):
    interview_id: int
    paper_name: str
    date: str
    score: Optional[float] = None

class InterviewAccessResponse(BaseModel):
    interview_id: int
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
    candidate: dict  # {"candidate": {...}}
    status: str
    scheduled_at: str
    score: Optional[float] = None

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    id: int
    email: str
    full_name: str
    role: str
    expires_at: str

class InterviewLinkResponse(BaseModel):
    interview_id: int
    admin: dict  # {"admin": {...}}
    candidate: dict  # {"candidate": {...}}
    access_token: str
    link: str
    scheduled_at: str
    warning: Optional[str] = None

class InterviewDetailRead(BaseModel):
    id: int
    admin: dict  # {"admin": {"id": ..., "email": ..., ...}}
    candidate: dict  # {"candidate": {"id": ..., "email": ..., ...}}
    paper_id: int
    paper_name: str
    schedule_time: str
    duration_minutes: int
    status: str
    total_score: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    access_token: str
    response_count: int
    proctoring_event_count: int
    enrollment_audio_url: Optional[str] = None

class UserDetailRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    resume_text: Optional[str] = None
    has_profile_image: bool
    has_face_embedding: bool
    created_interviews_count: int  # As admin
    participated_interviews_count: int  # As candidate
    profile_image_url: Optional[str] = None

class ProctoringLogItem(BaseModel):
    type: str
    time: str
    details: Optional[str] = None
    severity: Optional[str] = "info"
    triggered_warning: bool = False

class ResponseDetail(BaseModel):
    question: str
    answer: str
    score: str
    status: str # "Answered", "Skipped", "Pending AI"
    audio_url: Optional[str] = None

class DetailedResult(BaseModel):
    interview_id: int
    candidate: dict  # {"candidate": {...}}
    date: str
    score: str
    flags: bool
    details: List[ResponseDetail]
    proctoring_logs: List[ProctoringLogItem]

# Candidate Status Tracking Responses
class TimelineItem(BaseModel):
    """Single status change in the timeline"""
    status: str
    timestamp: str
    metadata: Optional[dict] = None

class ViolationSummary(BaseModel):
    """Details of a single violation"""
    type: str
    severity: str
    timestamp: str
    details: Optional[str] = None

class WarningInfo(BaseModel):
    """Warning system information"""
    total_warnings: int
    warnings_remaining: int
    max_warnings: int
    violations: List[ViolationSummary]

class ProgressInfo(BaseModel):
    """Interview progress information"""
    questions_answered: int
    total_questions: int
    current_question_id: Optional[int] = None

class CandidateStatusResponse(BaseModel):
    """Complete status response for a single interview"""
    interview_id: int
    candidate: dict  # {"candidate": {...}}
    current_status: Optional[str] = None
    timeline: List[TimelineItem]
    warnings: WarningInfo
    progress: ProgressInfo
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    last_activity: Optional[str] = None

class LiveStatusItem(BaseModel):
    """Lightweight status item for batch live status view"""
    interview_id: int
    candidate: dict  # {"candidate": {...}}
    current_status: Optional[str] = None
    warning_count: int
    warnings_remaining: int
    is_suspended: bool
    last_activity: Optional[str] = None
    progress_percent: float  # Calculated as (answered/total) * 100

