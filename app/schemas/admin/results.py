from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..shared.user import UserNested

class AdminAnswerAnswerShort(BaseModel):
    id: int
    interview_result_id: int
    candidate_answer: str = ""
    feedback: str = ""
    score: float = 0.0
    audio_path: str = ""
    transcribed_text: str = ""
    timestamp: datetime

    class Config:
        from_attributes = True

class AdminQuestionWithAnswer(BaseModel):
    id: int
    paper_id: int
    content: str = ""
    question_text: str = ""
    topic: str = ""
    difficulty: str = "Medium"
    marks: int = 1
    response_type: str = "audio"
    answer: Optional[AdminAnswerAnswerShort] = None
    coding_content: Optional[dict] = None

    class Config:
        from_attributes = True

class AdminPaperNested(BaseModel):
    id: int
    name: str
    description: str = ""
    admin_user: Optional[int] = None
    question_count: int = 0
    total_marks: int = 0
    created_at: datetime
    questions: List[AdminQuestionWithAnswer] = []

    class Config:
        from_attributes = True

class AdminProctoringEvent(BaseModel):
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    allow_copy_paste: bool = False
    allow_question_navigation: bool = False

    class Config:
        from_attributes = True

class GetInterviewResultResponse(BaseModel):
    id: int
    access_token: str
    invite_link: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[AdminPaperNested] = None
    coding_paper: Optional[AdminPaperNested] = None # Or specialized CodingPaper if needed
    schedule_time: Optional[datetime] = None
    duration_minutes: int = 1440
    max_questions: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    response_count: int = 0
    last_activity: Optional[datetime] = None
    result_status: str = "PENDING"
    max_marks: float = 0.0
    total_score: float = 0.0
    enrollment_audio_path: Optional[str] = None
    enrollment_audio_url: Optional[str] = None
    is_completed: bool = False
    proctoring_event: Optional[AdminProctoringEvent] = None

    class Config:
        from_attributes = True

class UpdateResultRequest(BaseModel):
    result_status: Optional[str] = None
    total_score: Optional[float] = None
    feedback: Optional[str] = None
