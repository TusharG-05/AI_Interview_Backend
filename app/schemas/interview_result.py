from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .interview_responses import (
    LoginUserNested as UserNested,
    QuestionPaperData as QuestionPaperNested,
    QuestionNested,
    CodingQuestionNested,
    CodingPaperNested
)

class InterviewSessionNested(BaseModel):
    id: int
    access_token: str
    invite_link: Optional[str] = None
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    question_paper: Optional[QuestionPaperNested] = None
    coding_paper: Optional[CodingPaperNested] = None
    schedule_time: Optional[datetime] = None
    duration_minutes: int = 1440
    max_questions: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    total_score: Optional[float] = None
    current_status: Optional[str] = None
    last_activity: Optional[datetime] = None
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False

class AnswersNested(BaseModel):
    id: int
    interview_result_id: int
    question: Optional[QuestionNested] = None
    coding_question: Optional[CodingQuestionNested] = None
    
    candidate_answer: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[float] = None
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class InterviewResultDetail(BaseModel):
    id: int
    interview: InterviewSessionNested
    interview_response: List[AnswersNested] = []
    result_status: str
    total_score: Optional[float] = None
    created_at: datetime
    proctoring_logs: List = [] 

class InterviewResultBrief(BaseModel):
    id: int
    interview: InterviewSessionNested
    result_status: str
    total_score: Optional[float] = None
    created_at: datetime
    proctoring_logs: List = []
