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

class CandidateStatus(str, Enum):
    """Tracks detailed lifecycle status of a candidate through the interview process"""
    INVITED = "invited"  # Email sent
    LINK_ACCESSED = "link_accessed"  # Candidate opened interview link
    AUTHENTICATED = "authenticated"  # Candidate logged in (future use)
    ENROLLMENT_STARTED = "enrollment_started"  # Selfie/enrollment in progress
    ENROLLMENT_COMPLETED = "enrollment_completed"  # Ready to start interview
    INTERVIEW_ACTIVE = "interview_active"  # Currently answering questions
    INTERVIEW_PAUSED = "interview_paused"  # Disconnected/paused
    INTERVIEW_COMPLETED = "interview_completed"  # Successfully finished
    SUSPENDED = "suspended"  # Suspended due to violations

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: UserRole = Field(default=UserRole.CANDIDATE)
    is_active: bool = Field(default=True)  # Soft delete flag
    resume_text: Optional[str] = Field(default=None)  # Stored extracted text
    profile_image: Optional[str] = Field(default=None) # Path to uploaded selfie (Legacy)
    profile_image_bytes: Optional[bytes] = Field(default=None) # Binary store for selfie
    face_embedding: Optional[str] = Field(default=None) # JSON/CSV string of the ArcFace vector
    
    # Relationships
    question_papers: List["QuestionPaper"] = Relationship(back_populates="admin")

class QuestionPaper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    admin_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    admin: User = Relationship(back_populates="question_papers")
    questions: List["Questions"] = Relationship(back_populates="paper")
    sessions: List["InterviewSession"] = Relationship(back_populates="paper")

class Questions(SQLModel, table=True):
    """Formerly named 'QuestionGroup'"""
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: Optional[int] = Field(default=None, foreign_key="questionpaper.id")
    content: Optional[str] = None
    question_text: Optional[str] = None # Legacy support
    topic: Optional[str] = None
    difficulty: str = Field(default="Medium")
    marks: int = Field(default=1)
    response_type: str = Field(default="audio") # Options: audio, text, both

    paper: Optional[QuestionPaper] = Relationship(back_populates="questions")
    responses: List["InterviewResponse"] = Relationship(back_populates="question")
    session_questions: List["SessionQuestion"] = Relationship(back_populates="question")

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Scheduler Info 
    access_token: str = Field(unique=True, index=True, default_factory=lambda: uuid.uuid4().hex)
    admin_id: int = Field(foreign_key="user.id")
    candidate_id: int = Field(foreign_key="user.id")
    paper_id: int = Field(foreign_key="questionpaper.id")
    
    # Timing
    schedule_time: datetime
    duration_minutes: int = Field(default=180) # 3 Hours default
    max_questions: Optional[int] = None  # Limit questions per interview, None = use all
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # State
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    total_score: Optional[float] = None
    
    # Candidate Status Tracking (NEW)
    current_status: Optional[CandidateStatus] = Field(default=None)  # Detailed lifecycle status
    last_activity: Optional[datetime] = None  # Last activity timestamp
    
    # Warning System (NEW)
    warning_count: int = Field(default=0)  # Current warning count
    max_warnings: int = Field(default=3)  # Maximum warnings before suspension
    is_suspended: bool = Field(default=False)  # Suspension flag
    suspension_reason: Optional[str] = None  # Reason for suspension
    suspended_at: Optional[datetime] = None  # Suspension timestamp
    
    # Legacy/Enrollment
    enrollment_audio_path: Optional[str] = None
    candidate_name: Optional[str] = None # Optional fallback
    is_completed: bool = Field(default=False) 
    
    # Relationships
    admin: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.admin_id"})
    candidate: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.candidate_id"})
    paper: QuestionPaper = Relationship(back_populates="sessions")
    
    responses: List["InterviewResponse"] = Relationship(back_populates="session")
    proctoring_events: List["ProctoringEvent"] = Relationship(back_populates="session")
    selected_questions: List["SessionQuestion"] = Relationship(back_populates="session")
    status_timeline: List["StatusTimeline"] = Relationship(back_populates="session")

class SessionQuestion(SQLModel, table=True):
    """Links sessions to their randomly assigned subset of questions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    question_id: int = Field(foreign_key="questions.id")
    sort_order: int = Field(default=0)
    
    session: InterviewSession = Relationship(back_populates="selected_questions")
    question: Questions = Relationship(back_populates="session_questions")

class ProctoringEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    event_type: str 
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Severity and Warning Tracking (NEW)
    severity: str = Field(default="info")  # Options: "info", "warning", "critical"
    triggered_warning: bool = Field(default=False)  # Whether this event added a warning
    
    session: InterviewSession = Relationship(back_populates="proctoring_events")

class StatusTimeline(SQLModel, table=True):
    """Tracks status changes throughout the interview lifecycle"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    status: CandidateStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_data: Optional[str] = None  # JSON string for additional context (renamed from metadata)
    
    session: InterviewSession = Relationship(back_populates="status_timeline")

class InterviewResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    question_id: int = Field(foreign_key="questions.id")
    
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
    question: Questions = Relationship(back_populates="responses")


# Rebuild models
User.model_rebuild()
QuestionPaper.model_rebuild()
Questions.model_rebuild()
InterviewSession.model_rebuild()
SessionQuestion.model_rebuild()
InterviewResponse.model_rebuild()
ProctoringEvent.model_rebuild()
StatusTimeline.model_rebuild()
