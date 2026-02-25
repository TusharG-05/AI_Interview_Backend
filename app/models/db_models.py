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
    resume_text: Optional[str] = Field(default=None)   # Stored extracted text
    access_token: Optional[str] = Field(default=None)  # Optional user-level access token
    profile_image: Optional[str] = Field(default=None)  # Path to uploaded selfie (Legacy)
    profile_image_bytes: Optional[bytes] = Field(default=None)  # Binary store for selfie
    face_embedding: Optional[str] = Field(default=None)  # JSON/CSV string of the ArcFace/SFace vector

    # Relationships
    question_papers: List["QuestionPaper"] = Relationship(back_populates="admin")

class QuestionPaper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")  # Not null; default empty string
    adminUser: Optional[int] = Field(default=None, foreign_key="user.id", alias="admin_id")  # Renamed from admin_id
    question_count: int = Field(default=0)   # Cached count (updated on add/remove)
    total_marks: int = Field(default=0)      # Cached total marks (updated on add/remove)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    admin: Optional[User] = Relationship(back_populates="question_papers")
    questions: List["Questions"] = Relationship(
        back_populates="paper",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    sessions: List["InterviewSession"] = Relationship(back_populates="paper")

    class Config:
        populate_by_name = True

class Questions(SQLModel, table=True):
    """Formerly named 'QuestionGroup'"""
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="questionpaper.id")  # Not null; required
    content: str = Field(default="string")          # Not null; default 'string'
    question_text: str = Field(default="string")    # Not null; legacy sync of content
    topic: str = Field(default="General")           # Not null; default 'General'
    difficulty: str = Field(default="Medium")
    marks: int = Field(default=1)
    response_type: str = Field(default="audio")  # Options: audio, text, both

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
    admin_id: int = Field(foreign_key="user.id")      # Points to sentinel if admin deleted
    candidate_id: int = Field(foreign_key="user.id")  # Points to sentinel if candidate deleted
    paper_id: int = Field(foreign_key="questionpaper.id")

    # Timing
    schedule_time: datetime
    duration_minutes: int = Field(default=1440)  # 1 Day default
    max_questions: Optional[int] = None   # None = use all questions
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # State
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    total_score: Optional[float] = None

    # Candidate Status Tracking
    current_status: Optional[CandidateStatus] = Field(default=None)
    last_activity: Optional[datetime] = None

    # Warning System
    warning_count: int = Field(default=0)
    max_warnings: int = Field(default=3)
    is_suspended: bool = Field(default=False)
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None

    # Enrollment
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = Field(default=False)

    # Relationships
    admin: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.admin_id"})
    candidate: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.candidate_id"})
    paper: QuestionPaper = Relationship(back_populates="sessions")

    # Cascade delete when interview is deleted
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
    details: str = Field(default="")  # Not null; default empty string
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Severity and Warning Tracking
    severity: str = Field(default="info")  # Options: "info", "warning", "critical"
    triggered_warning: bool = Field(default=False)

    session: InterviewSession = Relationship(back_populates="proctoring_events")

class StatusTimeline(SQLModel, table=True):
    """Tracks status changes throughout the interview lifecycle"""
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"))
    )
    status: CandidateStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_data: str = Field(default="{}")  # Not null; default empty JSON

    session: InterviewSession = Relationship(back_populates="status_timeline")

class InterviewResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewsession.id", ondelete="CASCADE"), unique=True)
    )
    total_score: float = Field(default=0.0)  # Not null; default 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: "InterviewSession" = Relationship(back_populates="result")
    answers: List["Answers"] = Relationship(
        back_populates="interview_result",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Answers(SQLModel, table=True):
    """Formerly named 'InterviewResponse'"""
    __tablename__ = "answers"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_result_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewresult.id", ondelete="CASCADE"))
    )
    question_id: int = Field(foreign_key="questions.id")

    # Kept nullable: audio answers have no text initially; text answers have no audio
    candidate_answer: Optional[str] = None
    feedback: Optional[str] = None       # Filled after AI evaluation
    score: Optional[float] = None        # Filled after AI evaluation
    audio_path: Optional[str] = None     # Only for audio-type answers
    transcribed_text: Optional[str] = None  # Filled after STT

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
