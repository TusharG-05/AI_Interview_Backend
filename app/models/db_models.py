from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel, Relationship, Column, ForeignKey, Integer
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
    SELFIE_UPLOADED = "selfie_uploaded" # Selfie verification uploaded
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
    access_token: Optional[str] = Field(default="")
    resume_text: Optional[str] = Field(default=None)  # Stored extracted text
    profile_image: Optional[str] = Field(default=None) # Path to uploaded selfie (Legacy)
    profile_image_bytes: Optional[bytes] = Field(default=None) # Binary store for selfie
    face_embedding: Optional[str] = Field(default=None) # JSON/CSV string of the ArcFace/Sface vector
    
    # Relationships
    question_papers: List["QuestionPaper"] = Relationship(back_populates="admin")

class QuestionPaper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    adminUser: Optional[int] = Field(default=None, foreign_key="user.id")  # Nullable to preserve papers when admin deleted
    question_count: int = Field(default=0)
    total_marks: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    admin: Optional[User] = Relationship(back_populates="question_papers")
    questions: List["Questions"] = Relationship(
        back_populates="paper",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    sessions: List["InterviewSession"] = Relationship(back_populates="paper")

class Questions(SQLModel, table=True):
    """Formerly named 'QuestionGroup'"""
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: Optional[int] = Field(default=None, foreign_key="questionpaper.id")
    content: str = Field(default="")
    question_text: str = Field(default="") # Legacy support
    topic: str = Field(default="")
    difficulty: str = Field(default="Medium")
    marks: int = Field(default=1)
    response_type: str = Field(default="audio") # Options: audio, text, both

    paper: Optional[QuestionPaper] = Relationship(back_populates="questions")
    answers: List["Answers"] = Relationship(
        back_populates="question", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    session_questions: List["SessionQuestion"] = Relationship(
        back_populates="question", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Scheduler Info 
    access_token: str = Field(unique=True, index=True, default_factory=lambda: uuid.uuid4().hex)
    invite_link: Optional[str] = None
    admin_id: Optional[int] = Field(foreign_key="user.id", nullable=True)  # Nullable to preserve history when admin deleted
    candidate_id: Optional[int] = Field(foreign_key="user.id", nullable=True) # Nullable to preserve history when candidate deleted
    paper_id: int = Field(foreign_key="questionpaper.id")
    
    # Timing
    schedule_time: datetime
    duration_minutes: int = Field(default=1440) # 1 Day default
    max_questions: int = Field(default=0)  # Limit questions per interview, 0 = use all
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # State
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    total_score: Optional[float] = None
    
    # Candidate Status Tracking (NEW)
    current_status: str = Field(default="")  # Detailed lifecycle status
    last_activity: datetime = Field(default_factory=datetime.utcnow)  # Last activity timestamp
    
    # Warning System (NEW)
    warning_count: int = Field(default=0)  # Current warning count
    max_warnings: int = Field(default=3)  # Maximum warnings before suspension
    is_suspended: bool = Field(default=False)  # Suspension flag
    suspension_reason: Optional[str] = None  # Reason for suspension
    suspended_at: Optional[datetime] = None  # Suspension timestamp
    
    # Legacy/Enrollment
    enrollment_audio_path: Optional[str] = None
    candidate_name: Optional[str] = None # Optional fallback for deleted candidate
    admin_name: Optional[str] = None  # Preserve admin name when admin is deleted
    is_completed: bool = Field(default=False) 
    
    # Relationships
    admin: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.admin_id"})
    candidate: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.candidate_id"})
    paper: QuestionPaper = Relationship(back_populates="sessions")
    
    # Cascade delete when interview is deleted (not when user is deleted)
    result: Optional["InterviewResult"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    proctoring_events: List["ProctoringEvent"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    selected_questions: List["SessionQuestion"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    status_timeline: List["StatusTimeline"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class SessionQuestion(SQLModel, table=True):
    """Links sessions to their randomly assigned subset of questions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"))
    )
    question_id: int = Field(foreign_key="questions.id")
    sort_order: int = Field(default=0)
    
    session: InterviewSession = Relationship(back_populates="selected_questions")
    question: Questions = Relationship(back_populates="session_questions")

class ProctoringEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"))
    )
    event_type: str 
    details: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Severity and Warning Tracking (NEW)
    severity: str = Field(default="info")  # Options: "info", "warning", "critical"
    triggered_warning: bool = Field(default=False)  # Whether this event added a warning
    
    session: InterviewSession = Relationship(back_populates="proctoring_events")

class StatusTimeline(SQLModel, table=True):
    """Tracks status changes throughout the interview lifecycle"""
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"))
    )
    status: CandidateStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_data: str = Field(default="")  # JSON string for additional context (renamed from metadata)
    
    session: InterviewSession = Relationship(back_populates="status_timeline")

class InterviewResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"), unique=True)
    )
    total_score: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    session: "InterviewSession" = Relationship(back_populates="result")
    answers: List["Answers"] = Relationship(
        back_populates="interview_result",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Answers(SQLModel, table=True):
    """Formerly named 'InterviewResponse'"""
    # Renamed table explicitly to handle migration if needed, but for clarity using table name default (answers)
    __tablename__ = "answers"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_result_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewresult.id", ondelete="CASCADE"))
    )
    question_id: int = Field(foreign_key="questions.id")
    
    # Legacy fields mapping
    candidate_answer: str = Field(default="") # Renamed from answer_text
    feedback: str = Field(default="") # Renamed from evaluation_text
    score: float = Field(default=0.0)
    
    # Audio fields (Persisted)
    audio_path: str = Field(default="")
    transcribed_text: str = Field(default="")
    
    # Keeping timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    interview_result: InterviewResult = Relationship(back_populates="answers")
    question: Questions = Relationship(back_populates="answers")


# Rebuild models
User.model_rebuild()
QuestionPaper.model_rebuild()
Questions.model_rebuild()
InterviewSession.model_rebuild()
SessionQuestion.model_rebuild()
InterviewResult.model_rebuild()
Answers.model_rebuild()
ProctoringEvent.model_rebuild()
StatusTimeline.model_rebuild()
