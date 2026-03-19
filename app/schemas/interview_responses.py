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

class QuestionWithAnswer(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str
    question_text: str
    topic: str
    answer: Optional[AnswerShort] = None  # Nested & Optional (lowercase per request)
    difficulty: str
    marks: int
    response_type: str
    coding_content: Optional[dict] = None  # Added for admin results consistency

class CodingQuestionWithAnswer(BaseModel):
    id: int
    paper_id: Optional[int] = None
    title: str
    problem_statement: str
    examples: List[Any] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    answer: Optional[AnswerShort] = None  # Lowercase 'answer' per request
    topic: str
    difficulty: str
    marks: int

class QuestionNested(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str
    question_text: str
    topic: str
    difficulty: str
    marks: int
    response_type: str

class PaperNested(BaseModel):
    id: int
    name: str
    description: str
    admin_user: Optional[UserNested] = None
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionWithAnswer] = []

class PaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionWithAnswer] = []
class CodingQuestionNested(BaseModel):
    id: int
    paper_id: Optional[int] = None
    title: str
    problem_statement: str
    examples: List[Any] = []
    constraints: List[str] = []
    starter_code: str
    topic: str
    difficulty: str
    marks: int

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for field in ("examples", "constraints"):
                raw = data.get(field)
                if isinstance(raw, str):
                    try:
                        data[field] = _json.loads(raw)
                    except:
                        data[field] = [] if field == "examples" else []
                elif raw is None:
                    data[field] = [] if field == "examples" else []
        return data

class CodingPaperNested(BaseModel):
    id: int
    name: str
    description: str
    admin_user: Optional[UserNested] = None
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[CodingQuestionWithAnswer] = []

class CodingPaperNestedWithoutAdmin(BaseModel):
    id: int
    name: str
    description: str
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[CodingQuestionWithAnswer] = []
    
class LoginUserNested(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None

class InterviewAccessResponse(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[LoginUserNested] = None
    candidate_user: Optional[LoginUserNested] = None
    paper: Optional[PaperNestedWithoutAdmin] = None
    coding_paper: Optional[CodingPaperNestedWithoutAdmin] = None
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
    result_status: Optional[str] = "PENDING"

class TabSwitchRequest(BaseModel):
    event_type: str  # "TAB_SWITCH" or "TAB_RETURN"

class QuestionData(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str
    question_text: str
    topic: str
    difficulty: str
    marks: int
    response_type: str
    coding_content: Optional[dict] = None  # Populated for response_type='code' questions

    @model_validator(mode="after")
    def populate_coding_content(self) -> "QuestionData":
        """If this is a code-type question with JSON content, parse it into coding_content."""
        if self.response_type == "code" and self.coding_content is None and self.content:
            try:
                parsed = _json.loads(self.content)
                if isinstance(parsed, dict) and "title" in parsed:
                    self.coding_content = parsed
            except (_json.JSONDecodeError, TypeError):
                pass
        return self

class QuestionPaperData(BaseModel):
    id: int
    name: str
    description: str
    admin_user: Union[UserNested, int]  # Handles object or FK int depending on endpoint
    question_count: Optional[int] = None
    questions: Optional[List[QuestionWithAnswer]] = None
    total_marks: Optional[int] = None
    created_at: datetime

class AnswersData(BaseModel):
    id: int
    interview_result_id: int
    question: QuestionData
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class CodingQuestionBasic(BaseModel):
    id: int
    paper_id: int
    title: str
    problem_statement: str
    examples: List[dict] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    topic: str
    difficulty: str
    marks: int

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        """Parse JSON-encoded examples and constraints strings into Python lists."""
        if isinstance(data, dict):
            # Already a dict, handle potential string fields within it
            data = dict(data)
            for field in ("examples", "constraints"):
                raw = data.get(field)
                if isinstance(raw, str):
                    try:
                        data[field] = _json.loads(raw)
                    except (_json.JSONDecodeError, TypeError):
                        data[field] = []
        return data

class CodingAnswersData(BaseModel):
    id: int
    interview_result_id: int
    coding_question: CodingQuestionBasic
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class AnswersDataAdmin(BaseModel):
    id: int
    interview_result_id: int
    question: Optional[QuestionData] = None  # Lowercase q specifically requested for admin results
    coding_question: Optional[CodingQuestionNested] = None
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class InterviewSessionData(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[QuestionPaperData] = None
    coding_paper: Optional[CodingPaperNested] = None
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
    allow_copy_paste: bool = False
    allow_question_navigate: bool = False
    tab_switch_count: int = 0
    tab_switch_timestamp: Optional[datetime] = None
    tab_warning_active: bool = False
    result_status: Optional[str] = "PENDING"

class AdminResultData(BaseModel):
    id: int
    interview: InterviewSessionData
    total_score: float
    result_status: Optional[str] = "PENDING"
    created_at: datetime
