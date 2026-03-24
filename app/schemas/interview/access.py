from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..shared.user import UserNested

class AnswerShort(BaseModel):
    id: int
    interview_result_id: int
    candidate_answer: str = ""
    feedback: str = ""
    score: float = 0.0
    audio_path: str = ""
    transcribed_text: str = ""
    timestamp: datetime

class QuestionWithAnswer(BaseModel):
    id: int
    paper_id: int
    content: str = ""
    question_text: str = ""
    topic: str = ""
    answer: Optional[AnswerShort] = None
    difficulty: str = "Medium"
    marks: int = 1
    response_type: str = "audio"
    coding_content: Optional[dict] = None

class CodingQuestionWithAnswer(BaseModel):
    id: int
    paper_id: int
    title: str = ""
    problem_statement: str = ""
    examples: List[dict] = []
    constraints: List[str] = []
    starter_code: str = ""
    answer: Optional[AnswerShort] = None
    topic: str = "Algorithms"
    difficulty: str = "Medium"
    marks: int = 0

class PaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str = ""
    question_count: int = 0
    total_marks: int = 0
    created_at: datetime
    questions: List[QuestionWithAnswer] = []

    class Config:
        from_attributes = True

class CodingPaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str = ""
    question_count: int = 0
    total_marks: int = 0
    created_at: datetime
    team_id: Optional[int] = None
    questions: List[CodingQuestionWithAnswer] = []

    class Config:
        from_attributes = True

class AccessInterviewResponse(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[PaperNestedWithoutAdmin] = None
    coding_paper: Optional[CodingPaperNestedWithoutAdmin] = None
    schedule_time: datetime
    duration_minutes: int
    max_questions: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    interview_round: Optional[str] = None
    response_count: int = 0
    last_activity: datetime
    result_status: str = "PENDING"
    max_marks: float = 0.0
    total_score: Optional[float] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False
    tab_switch_count: int = 0
    tab_warning_active: bool = False
    proctoring_event: Optional["ProctoringEvent"] = None

    class Config:
        from_attributes = True

class ProctoringEvent(BaseModel):
    id: int
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    allow_copy_paste: bool = False
    allow_question_navigation: bool = False

    class Config:
        from_attributes = True
