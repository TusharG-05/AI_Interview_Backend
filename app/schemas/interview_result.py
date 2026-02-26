from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class UserNested(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    profile_image: Optional[str] = None

class QuestionPaperNested(BaseModel):
    id: int
    name: str
    description: str = ""
    adminUser: Optional[int] = None
    question_count: int = 0
    total_marks: int = 0
    created_at: datetime

class QuestionNested(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str
    marks: int
    response_type: str

class InterviewSessionNested(BaseModel):
    id: int
    access_token: str
    invite_link: Optional[str] = None
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    question_paper: Optional[QuestionPaperNested] = None
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
    total_score: Optional[float] = None
    created_at: datetime
    proctoring_logs: List = [] 

class InterviewResultBrief(BaseModel):
    id: int
    interview: InterviewSessionNested
    total_score: Optional[float] = None
    created_at: datetime
    proctoring_logs: List = []   
