from typing import Optional, List, Any
from pydantic import BaseModel, Field, model_validator
from .user_schemas import UserNested
from .interview_result import QuestionPaperNested
from .team_schemas import TeamReadBasic
import json as _json

# Team Responses
# TeamReadBasic moved to team_schemas.py

class TeamRead(TeamReadBasic):
    users: List["UserRead"] = []  # Full nested users

class HistoryItem(BaseModel):
    interview_id: int
    access_token: str
    paper_name: str
    date: str
    status: str
    score: Optional[float] = None
    duration_minutes: Optional[int] = None
    max_questions: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    warning_count: int = 0
    is_completed: bool = False
    current_status: Optional[str] = None
    allow_copy_paste: bool = False



class QuestionRead(BaseModel):
    id: int
    content: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str
    marks: int
    response_type: str

# --- Coding Question Schemas (structured content) ---

class CodingExample(BaseModel):
    """A single input/output example for a coding problem."""
    input: str
    output: str
    explanation: Optional[str] = None

class CodingContent(BaseModel):
    """Structured body of a LeetCode-style coding problem."""
    title: str
    problem_statement: str
    examples: List[CodingExample] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None

class CodingQuestionRead(BaseModel):
    """
    A question whose `content` field is a structured coding problem object
    rather than a raw JSON string.

    During serialisation the raw JSON stored in the database is parsed
    automatically by the model validator below.
    """
    id: int
    content: Optional[CodingContent] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str
    marks: int
    response_type: str

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, data: Any) -> Any:
        """
        If `content` is a JSON string, decode it into a CodingContent dict so
        Pydantic can validate it as a nested object.  Silently falls back to
        None when the string cannot be parsed.
        """
        raw = data.get("content") if isinstance(data, dict) else None
        if isinstance(raw, str):
            try:
                data = dict(data)  # make mutable copy
                data["content"] = _json.loads(raw)
            except (_json.JSONDecodeError, TypeError):
                data = dict(data)
                data["content"] = None
        return data

class CodingPaperRead(BaseModel):
    """A question paper whose questions list uses CodingQuestionRead."""
    id: int
    name: str
    description: Optional[str] = None
    question_count: int = 0
    total_marks: int = 0
    questions: List[CodingQuestionRead] = []
    created_at: str


# --- Dedicated Coding Question Paper (new table) response schemas ---

class CodingQuestionFull(BaseModel):
    """
    Full representation of a CodingQuestions row.
    `examples` and `constraints` are returned as parsed Python lists.
    """
    id: int
    paper_id: int
    title: str
    problem_statement: str
    examples: List[Any] = []
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
            data = dict(data)
            for field in ("examples", "constraints"):
                raw = data.get(field)
                if isinstance(raw, str):
                    try:
                        data[field] = _json.loads(raw)
                    except (_json.JSONDecodeError, TypeError):
                        data[field] = []
        return data


class CodingPaperFull(BaseModel):
    """Full representation of a CodingQuestionPaper with all questions."""
    id: int
    name: str
    description: str = ""
    question_count: int = 0
    total_marks: int = 0
    questions: List[CodingQuestionFull] = []
    created_at: str
    created_by: Optional[UserNested] = None



class PaperRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    question_count: int = 0
    total_marks: int = 0
    questions: List[QuestionRead] = []
    created_at: str
class SessionRead(BaseModel):
    id: int
    admin_user: Optional[UserNested] = None
    candidate_user: UserNested
    status: str
    scheduled_at: str
    score: Optional[float] = None
    allow_copy_paste: bool = False
    interview_round: Optional[str] = None
    team_id: Optional[int] = None
class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    team: Optional[TeamReadBasic] = None

class UserMeResponse(BaseModel):
    """Complete user profile response for /auth/me endpoint"""
    id: int
    email: str
    full_name: str
    role: str
    profile_image: Optional[str] = None
    has_profile_image: bool = False
    has_face_embedding: bool = False
    resume_text: Optional[str] = None
    team: Optional[TeamReadBasic] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    id: int
    email: str
    full_name: str
    role: str
    expires_at: str
    team: Optional[TeamReadBasic] = None

class InterviewSessionDetail(BaseModel):
    id: int
    access_token: str
    admin_id: Optional[int] = None
    candidate_id: Optional[int] = None
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
    max_warnings: int
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False
    coding_paper_id: Optional[int] = None  # Linked coding question paper (if any)
    team_id: Optional[int] = None

class InterviewLinkResponse(BaseModel):
    interview: InterviewSessionDetail
    admin_user: UserNested
    candidate_user: UserNested
    access_token: str
    link: str
    scheduled_at: str
    warning: Optional[str] = None

class InterviewDetailRead(BaseModel):
    id: int
    admin_user: UserNested
    candidate_user: UserNested
    paper_id: int
    paper_name: str
    schedule_time: str
    duration_minutes: int
    status: str
    total_score: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    access_token: str
    response_count: int
    proctoring_event_count: int
    enrollment_audio_url: Optional[str] = None
    allow_copy_paste: bool = False

class QuestionPaperExpanded(BaseModel):
    id: int = 0
    name: str = ""
    description: str = ""
    admin_user: Optional[UserNested] = Field(default_factory=lambda: UserNested(id=0, email="", full_name="", role=""))
    question_count: int = 0
    questions: List[QuestionRead] = Field(default_factory=list)
    total_marks: int = 0
    created_at: str = ""

class CodingQuestionExpanded(BaseModel):
    id: int
    title: str
    problem_statement: str
    examples: List[Any] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    topic: str
    difficulty: str
    marks: int

class CodingPaperExpanded(BaseModel):
    id: int = 0
    name: str = ""
    description: str = ""
    admin_user: Optional[UserNested] = Field(default_factory=lambda: UserNested(id=0, email="", full_name="", role=""))
    question_count: int = 0
    questions: List[CodingQuestionExpanded] = Field(default_factory=list)
    total_marks: int = 0
    created_at: str = ""

class InterviewSessionExpanded(BaseModel):
    id: int
    access_token: str
    admin_user: Optional[UserNested] = None
    candidate_user: Optional[UserNested] = None
    paper: Optional[QuestionPaperExpanded] = None
    coding_paper: Optional[CodingPaperExpanded] = None
    interview_round: Optional[str] = None
    schedule_time: Optional[str] = ""
    duration_minutes: int = 0
    max_questions: int = 0
    status: Optional[str] = "SCHEDULED"
    total_score: Optional[float] = None
    current_status: str = ""
    last_activity: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    warning_count: int = 0
    max_warnings: int = 3
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = False
    allow_copy_paste: bool = False
    response_count: int = 0
    proctoring_event_count: int = 0
    enrollment_audio_url: Optional[str] = None
    team_id: Optional[int] = None

class UserDetailRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    resume_text: Optional[str] = None
    has_profile_image: bool
    has_face_embedding: bool
    created_interviews_count: int  # As admin
    participated_interviews_count: int  # As candidate
    profile_image_url: Optional[str] = None
    team: Optional[TeamReadBasic] = None

class ProctoringLogItem(BaseModel):
    type: str
    time: str
    details: Optional[str] = None
    severity: Optional[str] = "info"
    triggered_warning: bool = False

class ResponseDetail(BaseModel):
    question: str
    answer: str
    score: str
    status: str # "Answered", "Skipped", "Pending AI"
    audio_url: Optional[str] = None

class AnswerRead(BaseModel):
    id: int
    question: QuestionRead
    candidate_answer: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[float] = None
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    timestamp: Optional[str] = None



class DetailedResult(BaseModel):
    interview: InterviewSessionDetail # Full interview details
    candidate_user: UserNested
    answers: List[AnswerRead]
    date: str
    total_score: Optional[float] = None
    max_score: Optional[float] = None
    flags: bool
    details: List[ResponseDetail]
    proctoring_logs: List[ProctoringLogItem]

# Candidate Status Tracking Responses
class TimelineItem(BaseModel):
    """Single status change in the timeline"""
    status: str
    timestamp: str
    metadata: Optional[dict] = None

class ViolationSummary(BaseModel):
    """Details of a single violation"""
    type: str
    severity: str
    timestamp: str
    details: Optional[str] = None

class WarningInfo(BaseModel):
    """Warning system information"""
    total_warnings: int
    warnings_remaining: int
    max_warnings: int
    violations: List[ViolationSummary]

class ProgressInfo(BaseModel):
    """Interview progress information"""
    questions_answered: int
    total_questions: int
    current_question_id: Optional[int] = None

class CandidateStatusResponse(BaseModel):
    """Complete status response for a single interview"""
    interview: InterviewSessionDetail # Replaced interview_id with full object
    admin_user: Optional[UserNested] = None
    candidate_user: UserNested
    current_status: Optional[str] = None
    timeline: List[TimelineItem]
    warnings: WarningInfo
    progress: ProgressInfo
    is_suspended: bool
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    last_activity: Optional[str] = None

class LiveStatusItem(BaseModel):
    """Lightweight status item for batch live status view"""
    interview: InterviewSessionDetail # InterviewSession data
    admin_user: Optional[UserNested] = None
    candidate_user: UserNested
    current_status: Optional[str] = None
    warning_count: int
    warnings_remaining: int
    is_suspended: bool
    last_activity: Optional[str] = None
    progress_percent: float  # Calculated as (answered/total) * 100

