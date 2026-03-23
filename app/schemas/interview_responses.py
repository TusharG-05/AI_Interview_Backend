from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import json as _json
from .user_schemas import UserNested
from .team_schemas import TeamReadBasic

class AnswerShort(BaseModel):
    id: int
    interview_result_id: int
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class ProctoringEventRead(BaseModel):
    id: Optional[int] = None
    warning_count: int
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    allow_copy_paste: bool = False
    allow_question_navigation: bool = False

class QuestionWithAnswer(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str
    question_text: str
    topic: str
    answer: Optional[AnswerShort] = None
    difficulty: str
    marks: int
    response_type: str
    coding_content: Optional[dict] = None

    @model_validator(mode="after")
    def populate_coding_content(self) -> "QuestionWithAnswer":
        if self.response_type == "code" and self.coding_content is None and self.content:
            try:
                parsed = _json.loads(self.content)
                if isinstance(parsed, dict) and "title" in parsed:
                    self.coding_content = parsed
            except: pass
        return self

class CodingQuestionWithAnswer(BaseModel):
    id: int
    paper_id: Optional[int] = None
    title: str
    problem_statement: str
    examples: List[Any] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    answer: Optional[AnswerShort] = None
    topic: str
    difficulty: str
    marks: int

class PaperNestedWithAdminId(BaseModel):
    id: int
    name: str
    description: str
    admin_user: Optional[int] = None
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionWithAnswer] = []

class CodingPaperNestedWithAdmin(BaseModel):
    id: int
    name: str
    description: str
    admin_user: Optional[UserNested] = None
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[CodingQuestionWithAnswer] = []
    team_id: Optional[int] = None

class LoginUserNested(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None
    team: Optional[TeamReadBasic] = None

class InterviewAccessResponse(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[LoginUserNested] = None
    candidate_user: Optional[LoginUserNested] = None
    paper: Optional[PaperNestedWithAdminId] = None
    coding_paper: Optional[CodingPaperNestedWithAdmin] = None
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
    tab_warning_active: bool = False
    allow_copy_paste: bool = False
    allow_question_navigate: bool = False
    result_status: str = "PENDING"

class InterviewSessionData(BaseModel):
    id: int
    access_token: str
    invite_link: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[PaperNestedWithAdminId] = None
    coding_paper: Optional[CodingPaperNestedWithAdmin] = None
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
    proctoring_event: Optional[ProctoringEventRead] = None

def remove_none_values(obj: Any) -> Any:
    if isinstance(obj, list):
        return [remove_none_values(i) for i in obj if i is not None]
    elif isinstance(obj, dict):
        return {k: remove_none_values(v) for k, v in obj.items() if v is not None}
    return obj

# Compatibility Aliases
QuestionNested = QuestionWithAnswer
CodingQuestionNested = CodingQuestionWithAnswer
PaperNested = PaperNestedWithAdminId
QuestionPaperData = PaperNestedWithAdminId
CodingPaperNested = CodingPaperNestedWithAdmin
AnswersDataAdmin = AnswerShort

class QuestionData(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str

class QuestionPaperNested(BaseModel):
    id: int
    name: str

class CodingQuestionBasic(BaseModel):
    id: int
    title: str
    problem_statement: str
    difficulty: str
    marks: int

class PaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionWithAnswer] = []

class CodingPaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[CodingQuestionWithAnswer] = []

class AnswersData(BaseModel):
    id: int
    interview_result_id: int
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class CodingAnswersData(BaseModel):
    id: int
    interview_result_id: int
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime
