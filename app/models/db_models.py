from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel, Relationship, Column, ForeignKey, Integer
from enum import Enum
import uuid

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    CANDIDATE = "CANDIDATE"

class InterviewStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class InterviewRound(str, Enum):
    ROUND_1 = "ROUND_1"
    ROUND_2 = "ROUND_2"
    ROUND_3 = "ROUND_3"
    ROUND_4 = "ROUND_4"
    ROUND_5 = "ROUND_5"

class CandidateStatus(str, Enum):
    """Tracks detailed lifecycle status of a candidate through the interview process"""
    INVITED = "INVITED"  # Email sent
    LINK_ACCESSED = "LINK_ACCESSED"  # Candidate opened interview link
    AUTHENTICATED = "AUTHENTICATED"  # Candidate logged in (future use)
    SELFIE_UPLOADED = "SELFIE_UPLOADED" # Selfie verification uploaded
    ENROLLMENT_STARTED = "ENROLLMENT_STARTED"  # Selfie/enrollment in progress
    ENROLLMENT_COMPLETED = "ENROLLMENT_COMPLETED"  # Ready to start interview
    INTERVIEW_ACTIVE = "INTERVIEW_ACTIVE"  # Currently answering questions
    INTERVIEW_PAUSED = "INTERVIEW_PAUSED"  # Disconnected/paused
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"  # Successfully finished
    SUSPENDED = "SUSPENDED"  # Suspended due to violations

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
    team_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    )
    team: Optional["Team"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "User.team_id"}
    )
    question_papers: List["QuestionPaper"] = Relationship(back_populates="admin")


class Team(SQLModel, table=True):
    """A globally unique team created by a super admin (e.g. Python Team, React Team)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Globally unique
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: List["User"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"foreign_keys": "User.team_id"}
    )

class QuestionPaper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    admin_user: Optional[int] = Field(default=None, foreign_key="user.id")  # Nullable to preserve papers when admin deleted
    question_count: int = Field(default=0)
    total_marks: int = Field(default=0)
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
    paper_id: Optional[int] = Field(default=None, foreign_key="questionpaper.id", nullable=True)
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


class CodingQuestionPaper(SQLModel, table=True):
    """A question paper containing LeetCode-style coding problems."""
    __tablename__ = "codingquestionpaper"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    admin_user: Optional[int] = Field(default=None, foreign_key="user.id")  # Nullable to preserve papers when admin deleted
    question_count: int = Field(default=0)
    total_marks: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    admin: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "CodingQuestionPaper.admin_user", "primaryjoin": "CodingQuestionPaper.admin_user == User.id"}
    )
    questions: List["CodingQuestions"] = Relationship(
        back_populates="paper",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    sessions: List["InterviewSession"] = Relationship(
        back_populates="coding_paper",
        sa_relationship_kwargs={"primaryjoin": "InterviewSession.coding_paper_id == CodingQuestionPaper.id"}
    )

    class Config:
        populate_by_name = True


class CodingQuestions(SQLModel, table=True):
    """A single LeetCode-style coding problem belonging to a CodingQuestionPaper."""
    __tablename__ = "codingquestions"

    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(
        sa_column=Column(Integer, ForeignKey("codingquestionpaper.id", ondelete="CASCADE"), nullable=False)
    )
    # Problem content
    title: str = Field(default="")
    problem_statement: str = Field(default="")
    examples: str = Field(default="[]")        # JSON-encoded list of {input, output, explanation}
    constraints: str = Field(default="[]")     # JSON-encoded list of strings
    starter_code: str = Field(default="")
    # Meta
    topic: str = Field(default="Algorithms")
    difficulty: str = Field(default="Medium")
    marks: int = Field(default=6)

    # Relationships
    paper: Optional[CodingQuestionPaper] = Relationship(back_populates="questions")

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Scheduler Info
    access_token: str = Field(unique=True, index=True, default_factory=lambda: uuid.uuid4().hex)
    admin_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    )
    candidate_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    )
    invite_link: Optional[str] = None
    paper_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("questionpaper.id", ondelete="SET NULL"), nullable=True)
    )
    coding_paper_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("codingquestionpaper.id", ondelete="SET NULL"), nullable=True)
    )

    # Interview Round
    interview_round: Optional[InterviewRound] = Field(default=None)

    # Timing
    schedule_time: datetime
    duration_minutes: int = Field(default=1440)  # 1 Day default
    max_questions: int = Field(default=0)   # 0 = use all questions
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # State
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    total_score: Optional[float] = None

    # Candidate Status Tracking
    current_status: str = Field(default="")
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    # Warning System
    warning_count: int = Field(default=0)
    max_warnings: int = Field(default=3)
    is_suspended: bool = Field(default=False)
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None

    # Enrollment
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = Field(default=False)

    # Copy-Paste Control
    allow_copy_paste: bool = Field(default=False)
    
    # Relationships
    admin: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.admin_id"})
    candidate: User = Relationship(sa_relationship_kwargs={"foreign_keys": "InterviewSession.candidate_id"})
    paper: Optional[QuestionPaper] = Relationship(
        back_populates="sessions",
        sa_relationship_kwargs={"primaryjoin": "InterviewSession.paper_id == QuestionPaper.id"}
    )
    coding_paper: Optional["CodingQuestionPaper"] = Relationship(
        back_populates="sessions",
        sa_relationship_kwargs={"primaryjoin": "InterviewSession.coding_paper_id == CodingQuestionPaper.id"}
    )
    # team: Optional["Team"] = Relationship(back_populates="interview_sessions")

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
    details: str = Field(default="")
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
    result_status: str = Field(default="PENDING", title="Status: PENDING, PASS, or FAIL")
    total_score: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: "InterviewSession" = Relationship(back_populates="result")
    answers: List["Answers"] = Relationship(
        back_populates="interview_result",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    coding_answers: List["CodingAnswers"] = Relationship(
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
    question_id: Optional[int] = Field(default=None, foreign_key="questions.id")
    coding_question_id: Optional[int] = Field(default=None, foreign_key="codingquestions.id")

    # Kept nullable: audio answers have no text initially; text answers have no audio
    candidate_answer: str = Field(default="")
    feedback: str = Field(default="")       # Filled after AI evaluation
    score: float = Field(default=0.0)        # Filled after AI evaluation
    audio_path: str = Field(default="")     # Only for audio-type answers
    transcribed_text: str = Field(default="")  # Filled after STT

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interview_result: InterviewResult = Relationship(back_populates="answers")
    question: Optional[Questions] = Relationship(back_populates="answers")
    coding_question: Optional[CodingQuestions] = Relationship()


class CodingAnswers(SQLModel, table=True):
    """Answers specifically for coding questions."""
    __tablename__ = "codinganswers"

    id: Optional[int] = Field(default=None, primary_key=True)
    interview_result_id: int = Field(
        sa_column=Column(Integer, ForeignKey("interviewresult.id", ondelete="CASCADE"))
    )
    coding_question_id: int = Field(
        sa_column=Column(Integer, ForeignKey("codingquestions.id", ondelete="CASCADE"))
    )

    candidate_answer: str = Field(default="")
    feedback: str = Field(default="")
    score: float = Field(default=0.0)
    audio_path: str = Field(default="")
    transcribed_text: str = Field(default="")

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interview_result: InterviewResult = Relationship(back_populates="coding_answers")
    coding_question: CodingQuestions = Relationship()


# Rebuild models
User.model_rebuild()
Team.model_rebuild()
QuestionPaper.model_rebuild()
Questions.model_rebuild()
CodingQuestionPaper.model_rebuild()
CodingQuestions.model_rebuild()
InterviewSession.model_rebuild()
SessionQuestion.model_rebuild()
InterviewResult.model_rebuild()
Answers.model_rebuild()
ProctoringEvent.model_rebuild()
StatusTimeline.model_rebuild()
CodingAnswers.model_rebuild()
