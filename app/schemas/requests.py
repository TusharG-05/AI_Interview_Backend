from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from ..models.db_models import UserRole, InterviewRound



# Candidate Requests
class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None  # String, will be converted to UserRole
    resume_text: Optional[str] = None
    team_id: Optional[int] = None

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CANDIDATE
    team_id: Optional[int] = None

# Admin Requests
class InterviewScheduleCreate(BaseModel):
    candidate_id: int
    paper_id: Optional[int] = None         # Standard question paper (optional)
    coding_paper_id: Optional[int] = None  # Coding question paper (optional)
    interview_round: InterviewRound  # Required: e.g. ROUND_1, ROUND_2
    schedule_time: str # ISO format expected from frontend
    duration_minutes: int = 1440
    max_questions: Optional[int] = None  # Limit questions, None = use all
    allow_copy_paste: bool = False  # Whether candidate can copy/paste during interview

    @model_validator(mode="after")
    def at_least_one_paper(self) -> "InterviewScheduleCreate":
        """Ensure at least one of paper_id or coding_paper_id is provided."""
        if self.paper_id is None and self.coding_paper_id is None:
            raise ValueError(
                "At least one of 'paper_id' (standard questions) or "
                "'coding_paper_id' (coding questions) must be provided."
            )
        return self

# Team Requests (super admin only for create/update/delete)
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class InterviewUpdate(BaseModel):
    schedule_time: Optional[str] = None  # ISO format
    duration_minutes: Optional[int] = None
    status: Optional[str] = None  # 'scheduled', 'cancelled', etc.
    paper_id: Optional[int] = None  # Allow changing question paper
    max_questions: Optional[int] = None  # Update question limit
    allow_copy_paste: Optional[bool] = None  # Update copy/paste permission

class ResponseUpdate(BaseModel):
    """Update individual response within a result"""
    response_id: int
    score: Optional[float] = None
    evaluation_text: Optional[str] = None

class ResultUpdate(BaseModel):
    """Update overall result and individual responses"""
    result_status: Optional[str] = None  # "PENDING", "PASS", "FAIL"
    total_score: Optional[float] = None
    responses: Optional[list] = None  # List of ResponseUpdate dicts

# Interview Requests
class AnswerRequest(BaseModel):
    question: str
    answer: str

class PaperUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class QuestionUpdate(BaseModel):
    content: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None
    response_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    access_token: Optional[str] = None    
class QuestionCreate(BaseModel):
    content: str
    topic: Optional[str] = "General"
    difficulty: str = "Medium"
    marks: int = 1
    response_type: str = "audio"


class GeneratePaperRequest(BaseModel):
    ai_prompt: str = Field(..., min_length=5, description="Topic or job description to base questions on")
    years_of_experience: int = Field(..., ge=0, le=40, description="Candidate's expected years of experience")
    num_questions: int = Field(..., ge=1, le=50, description="Number of questions to generate")
    paper_name: Optional[str] = Field(None, description="Optional name for the question paper")


class GenerateCodingPaperRequest(BaseModel):
    ai_prompt: str = Field(
        ..., min_length=3,
        description="Topic area for the coding problems, e.g. 'Arrays and Hashing', 'Dynamic Programming'"
    )
    difficulty_mix: str = Field(
        default="mixed",
        description="Difficulty of problems: 'easy', 'medium', 'hard', or 'mixed'"
    )
    num_questions: int = Field(
        ..., ge=1, le=20,
        description="Number of coding problems to generate (max 20)"
    )
    paper_name: Optional[str] = Field(None, description="Optional name for the coding paper")

# --- Coding Question Paper (Dedicated Table) ---

class CodingPaperCreate(BaseModel):
    """Create a new dedicated coding question paper."""
    name: str = Field(..., min_length=1, description="Name of the coding paper")
    description: Optional[str] = Field(None, description="Optional description")


class CodingPaperUpdate(BaseModel):
    """Partially update a coding question paper."""
    name: Optional[str] = None
    description: Optional[str] = None


class CodingQuestionCreate(BaseModel):
    """Add a single LeetCode-style problem to a coding paper."""
    title: str = Field(..., min_length=1, description="Problem title")
    problem_statement: str = Field(..., min_length=10, description="Full problem description (markdown supported)")
    examples: List[dict] = Field(
        default_factory=list,
        description="List of {input, output, explanation} dicts"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="List of constraint strings"
    )
    starter_code: Optional[str] = Field(None, description="Language-agnostic starter function")
    topic: str = Field(default="Algorithms", description="Topic category")
    difficulty: str = Field(default="Medium", description="Easy / Medium / Hard")
    marks: int = Field(default=6, ge=1, description="Marks awarded for a correct solution")


class CodingQuestionUpdate(BaseModel):
    """Partially update a coding question."""
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    examples: Optional[List[dict]] = None
    constraints: Optional[List[str]] = None
    starter_code: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None

class CodingAnswerRequest(BaseModel):
    """Request schema for submitting a coding answer."""
    interview_id: int
    question_id: int
    answer_code: str
    feedback: Optional[str] = None
    score: Optional[float] = None
