from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import json as _json
from .user_schemas import UserNested

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
    admin_user: UserNested  # Always use UserNested object for consistency
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionNested]

class CodingQuestionNested(BaseModel):
    id: int
    paper_id: int
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
                        data[field] = []
        return data

class CodingPaperNested(BaseModel):
    id: int
    name: str
    description: str
    admin_user: UserNested  # Always use UserNested object for consistency
    question_count: int
    total_marks: int
    created_at: datetime
    coding_questions: List[CodingQuestionNested] = []

class LoginUserNested(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None
    team_id: Optional[int] = None

class InterviewAccessResponse(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None  # Consistent UserNested type
    candidate_user: Optional[UserNested] = None
    paper_id: Optional[PaperNested] = None
    coding_paper_id: Optional[CodingPaperNested] = None
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
    result_status: Optional[str] = "PENDING"

# --- End New Schemas ---

class QuestionData(BaseModel):
    id: int
    paper_id: int
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
    questions: Optional[List[QuestionData]] = None
    total_marks: Optional[int] = None
    created_at: datetime

class AnswersData(BaseModel):
    id: int
    interview_result_id: int
    question_id: QuestionData
    candidate_answer: str
    feedback: str
    score: float
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: datetime

class CodingAnswersData(BaseModel):
    id: int
    interview_result_id: int
    coding_question_id: CodingQuestionNested
    candidate_answer: str
    feedback: str
    score: float
    timestamp: datetime

class AnswersDataAdmin(BaseModel):
    id: int
    interview_result_id: int
    question_id: Optional[QuestionData] = None  # Lowercase q specifically requested for admin results
    coding_question_id: Optional[CodingQuestionNested] = None
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
    paper_id: Optional[QuestionPaperData] = None
    coding_paper_id: Optional[CodingPaperNested] = None
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
    result_status: Optional[str] = "PENDING"

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
    coding_question_id: CodingQuestionBasic
    candidate_answer: str
    feedback: str
    score: float
    audio_path: str
    transcribed_text: str
    timestamp: datetime

class AdminResultData(BaseModel):
    id: int
    interview_data: InterviewSessionData
    interview_responses: List[AnswersDataAdmin] = []
    coding_responses: List[CodingAnswersData] = []
    total_score: float
    result_status: Optional[str] = "PENDING"
    created_at: datetime
