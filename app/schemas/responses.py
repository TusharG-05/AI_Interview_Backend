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
    created_by: Optional[dict] = None # {"id": ..., "email": ..., "full_name": ..., "role": ...}

class SessionRead(BaseModel):
    id: int
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
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
    admin: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
    access_token: str
    link: str
    scheduled_at: str
    warning: Optional[str] = None

class InterviewDetailRead(BaseModel):
    id: int
    admin: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
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

class AnswerRead(BaseModel):
    id: int
    question_id: int
    candidate_answer: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[float] = None
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: Optional[str] = None

class InterviewSessionDetail(BaseModel):
    id: int
    access_token: str
    admin_id: Optional[int] = None
    candidate_id: Optional[int] = None
    paper_id: int
    schedule_time: str
    duration_minutes: int
    max_questions: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str
    total_score: Optional[float] = None
    current_status: Optional[str] = None
    last_activity: Optional[str] = None
    warning_count: int
    max_warnings: int
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    enrollment_audio_path: Optional[str] = None
    candidate_name: Optional[str] = None
    admin_name: Optional[str] = None
    is_completed: bool

class DetailedResult(BaseModel):
    interview: InterviewSessionDetail # Full interview details
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
    answers: List[AnswerRead]
    date: str
    total_score: Optional[float] = None
    max_score: Optional[float] = None
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
    interview: InterviewSessionDetail # Replaced interview_id with full object
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
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
    interview: InterviewSessionDetail # InterviewSession data
    candidate: dict  # {"id": ..., "email": ..., "full_name": ..., "role": ...}
    current_status: Optional[str] = None
    warning_count: int
    warnings_remaining: int
    is_suspended: bool
    last_activity: Optional[str] = None
    progress_percent: float  # Calculated as (answered/total) * 100

