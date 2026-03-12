from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import json as _json

class LoginUserNested(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None

# --- New Flattened Schemas for Interview Access API ---

class AdminNested(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None

class CandidateNested(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None

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
    adminUser: Union[AdminNested, int]  # Restore nested adminUser
    question_count: int
    total_marks: int
    created_at: datetime
    questions: List[QuestionNested]

class CodingQuestionNested(BaseModel):
    id: int
    paper_id: int
    title: str
    problem_statement: str
    examples: str
    constraints: str
    starter_code: str
    topic: str
    difficulty: str
    marks: int

class CodingPaperNested(BaseModel):
    id: int
    name: str
    description: str
    adminUser: Union[AdminNested, int] # Restore nested adminUser
    question_count: int
    total_marks: int
    created_at: datetime
    coding_questions: List[CodingQuestionNested]

class InterviewAccessResponse(BaseModel):
    id: int
    access_token: str
    admin: Optional[AdminNested] = None
    candidate: Optional[CandidateNested] = None
    paper: Optional[PaperNested] = None
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
    allow_copy_paste: bool = False
    result_status: Optional[str] = "PENDING"

class AdminResultData(BaseModel):
    id: int
    interviewData: InterviewSessionData
    Interview_response: List[AnswersDataAdmin] = []
    total_score: float
    result_status: Optional[str] = "PENDING"
    created_at: datetime
