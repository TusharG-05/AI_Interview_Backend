from typing import List, Optional, Any
from pydantic import BaseModel
from ..shared.user import UserNested

class TimelineItem(BaseModel):
    status: str
    timestamp: str
    metadata: Optional[dict] = None

class ViolationSummary(BaseModel):
    type: str
    severity: str
    timestamp: str
    details: Optional[str] = None

class WarningInfo(BaseModel):
    total_warnings: int
    warnings_remaining: int
    max_warnings: int
    violations: List[ViolationSummary] = []

class ProgressInfo(BaseModel):
    questions_answered: int
    total_questions: int
    current_question_id: Optional[int] = None

class AdminInterviewSessionDetail(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper_id: Optional[int] = None
    interview_round: Optional[str] = None
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
    allow_copy_paste: bool = False
    allow_question_navigate: bool = False
    max_warnings: int
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False
    coding_paper_id: Optional[int] = None
  
   

    class Config:
        from_attributes = True

class GetCandidateStatusResponse(BaseModel):
    interview: AdminInterviewSessionDetail
    admin_user: Optional[UserNested] = None
    candidate_user: UserNested
    current_status: Optional[str] = None
    timeline: List[TimelineItem] = []
    warnings: WarningInfo
    progress: ProgressInfo
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    last_activity: Optional[str] = None

    class Config:
        from_attributes = True

class LiveStatusItem(BaseModel):
    interview: AdminInterviewSessionDetail
    admin_user: Optional[UserNested] = None
    candidate_user: UserNested
    current_status: Optional[str] = None
    warning_count: int
    warnings_remaining: int
    is_suspended: bool
    last_activity: Optional[str] = None
    progress_percent: float

    class Config:
        from_attributes = True
