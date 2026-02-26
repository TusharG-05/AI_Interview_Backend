from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class LoginUserNested(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None

class QuestionData(BaseModel):
    id: int
    paper_id: int
    content: str
    question_text: str
    topic: str
    difficulty: str
    marks: int
    response_type: str
    
class QuestionPaperData(BaseModel):
    id: int
    name: str
    description: str
    adminUser: Union[LoginUserNested, int]  # Handles object or FK int depending on endpoint
    question_count: Optional[int] = None
    questions: Optional[List[QuestionData]] = None
    total_marks: Optional[int] = None
    created_at: datetime

class AnswersData(BaseModel):
    id: int
    interview_result_id: int
    Question_id: QuestionData  # Uppercase Q specifically requested for submit-answer
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class AnswersDataAdmin(BaseModel):
    id: int
    interview_result_id: int
    question_id: QuestionData  # Lowercase q specifically requested for admin results
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class InterviewSessionData(BaseModel):
    id: int
    access_token: str
    admin_id: Optional[LoginUserNested] = None
    candidate_id: Optional[LoginUserNested] = None
    paper_id: Optional[QuestionPaperData] = None
    schedule_time: datetime
    duration_minutes: int
    max_questions: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    total_score: Optional[float] = None
    current_status: str
    last_activity: datetime
    warning_count: int
    max_warnings: int
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool

class AdminResultData(BaseModel):
    id: int
    interviewData: InterviewSessionData
    Interview_response: List[AnswersDataAdmin] = []
    total_score: float
    created_at: datetime
