from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    CANDIDATE = "candidate"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: UserRole = Field(default=UserRole.CANDIDATE)
    resume_text: Optional[str] = Field(default=None)  # Stored extracted text
    profile_image: Optional[str] = Field(default=None) # Path to uploaded selfie
    
    # Relationships
    question_banks: List["QuestionBank"] = Relationship(back_populates="admin")

class QuestionBank(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    admin_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    admin: User = Relationship(back_populates="question_banks")
    questions: List["QuestionGroup"] = Relationship(back_populates="bank")
    sessions: List["InterviewSession"] = Relationship(back_populates="bank")

class QuestionGroup(SQLModel, table=True):
    """Formerly named 'Question'"""
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: Optional[int] = Field(default=None, foreign_key="questionbank.id")
    content: Optional[str] = None
    question_text: Optional[str] = None # Legacy support
    topic: Optional[str] = None
    difficulty: str = Field(default="Medium")
    reference_answer: Optional[str] = None # Legacy support
    marks: int = Field(default=1)
    
    bank: Optional[QuestionBank] = Relationship(back_populates="questions")
    responses: List["InterviewResponse"] = Relationship(back_populates="question")
    session_questions: List["SessionQuestion"] = Relationship(back_populates="question")

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Scheduler Info
    access_token: str = Field(unique=True, index=True, default_factory=lambda: uuid.uuid4().hex)
    admin_id: int = Field(foreign_key="user.id")
    candidate_id: int = Field(foreign_key="user.id")
    bank_id: int = Field(foreign_key="questionbank.id")
    
    # Timing
    schedule_time: datetime
    duration_minutes: int = Field(default=180) # 3 Hours default
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # State
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    total_score: Optional[float] = None
    
    # Legacy/Enrollment
    enrollment_audio_path: Optional[str] = None
    candidate_name: Optional[str] = None # Optional fallback
    is_completed: bool = Field(default=False) # Keep for backward compatibility logic
    
    # Relationships
    admin: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.admin_id"})
    candidate: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.candidate_id"})
    bank: QuestionBank = Relationship(back_populates="sessions")
    
    responses: List["InterviewResponse"] = Relationship(back_populates="session")
    proctoring_events: List["ProctoringEvent"] = Relationship(back_populates="session")
    selected_questions: List["SessionQuestion"] = Relationship(back_populates="session")

class SessionQuestion(SQLModel, table=True):
    """Links sessions to their randomly assigned subset of questions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    question_id: int = Field(foreign_key="questiongroup.id")
    sort_order: int = Field(default=0)
    
    session: InterviewSession = Relationship(back_populates="selected_questions")
    question: QuestionGroup = Relationship(back_populates="session_questions")

class ProctoringEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    event_type: str # e.g., "MULTIPLE_FACES", "Gaze Violation", "Unknown Person"
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    session: InterviewSession = Relationship(back_populates="proctoring_events")

class InterviewResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    question_id: int = Field(foreign_key="questiongroup.id")
    
    # Legacy fields
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    similarity_score: Optional[float] = None
    
    # New flow fields
    answer_text: Optional[str] = None
    evaluation_text: Optional[str] = None
    score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    session: InterviewSession = Relationship(back_populates="responses")
    question: QuestionGroup = Relationship(back_populates="responses")

# Aliases for legacy code
Question = QuestionGroup
CandidateResponse = InterviewResponse
InterviewRoom = None # Explicitly Removed

# Rebuild models to resolve forward references
User.model_rebuild()
QuestionBank.model_rebuild()
QuestionGroup.model_rebuild()
InterviewSession.model_rebuild()
SessionQuestion.model_rebuild()
InterviewResponse.model_rebuild()
ProctoringEvent.model_rebuild()
