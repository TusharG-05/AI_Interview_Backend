from typing import List, Optional, Union
from pydantic import BaseModel, Field, FieldSerializationInfo, field_serializer, field_validator
from datetime import datetime
from ..shared.user import UserNested
from ...models.db_models import UserRole, InterviewRound

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
        populate_by_name = True

class CodingQuestionExample(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class CodingQuestionWithAnswer(BaseModel):
    id: int
    paper_id: int
    title: str
    problem_statement: str
    examples: List[CodingQuestionExample] = []
    constraints: List[str] = []
    starter_code: str = ""
    answer: Optional[AdminAnswerAnswerShort] = None
    topic: str = "Algorithms"
    difficulty: str = "Medium"
    marks: int = 0

    class Config:
        from_attributes = True
        populate_by_name = True

class AdminQuestionWithAnswer(BaseModel):
    id: int
    paper_id: Optional[int] = None
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
        populate_by_name = True

class AdminPaperNested(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    question_count: int = 0
    total_marks: float = 0.0
    created_at: datetime
    team_id: Optional[int] = None
    questions: Optional[List[Union[AdminQuestionWithAnswer, CodingQuestionWithAnswer]]] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class AdminProctoringEvent(BaseModel):
    id: Optional[int] = None
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    allow_copy_paste: bool = False
    allow_question_navigation: bool = False

    class Config:
        from_attributes = True
        populate_by_name = True

class InterviewSessionNested(BaseModel):
    id: int
    access_token: str
    invite_link: Optional[str] = None
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[AdminPaperNested] = None
    coding_paper: Optional[AdminPaperNested] = None
    schedule_time: Optional[datetime] = None
    duration_minutes: int = 1440
    max_questions: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    total_score: Optional[float] = Field(default=0.0)
    current_status: Optional[str] = None
    last_activity: Optional[datetime] = None
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False

    class Config:
        from_attributes = True
        populate_by_name = True

class GetResultsResponse(BaseModel):
    id: Optional[int] = None
    interview_session_id: int
    interview_session: Optional[InterviewSessionNested] = None
    result_status: str = "PENDING"
    total_score: float = Field(default=0.0)
    feedback: str = ""
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class GetInterviewResultResponse(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[AdminPaperNested] = None
    coding_paper: Optional[AdminPaperNested] = None 
    schedule_time: Optional[datetime] = None
    duration_minutes: int = 1440
    max_questions: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    interview_round: Optional[Union[InterviewRound, str]] = None
    response_count: int = 0
    last_activity: Optional[datetime] = None
    result_status: str = "PENDING"
    max_marks: float = 0.0
    total_score: float = Field(default=0.0)
    enrollment_audio_path: Optional[str] = None
    enrollment_audio_url: Optional[str] = None
    is_completed: bool = False
    proctoring_event: Optional[AdminProctoringEvent] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class UpdateResultRequest(BaseModel):
    result_status: Optional[str] = None
    total_score: Optional[float] = Field(default=None)
    feedback: Optional[str] = None

class GetAdminResultsListResponse(BaseModel):
    id: int
    admin_user: UserNested
    candidate_user: UserNested
    status: str
    result_status: str = "PENDING"
    end_time: Optional[datetime] = None
    total_score: Optional[float] = None

    class Config:
        from_attributes = True
        populate_by_name = True
