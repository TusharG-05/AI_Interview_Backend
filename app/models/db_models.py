from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    CANDIDATE = "candidate"
    INTERVIEWER = "interviewer"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: UserRole = Field(default=UserRole.CANDIDATE)
    resume_text: Optional[str] = Field(default=None)
    profile_image: Optional[str] = Field(default=None)
    
    rooms_created: List["InterviewRoom"] = Relationship(back_populates="admin", sa_relationship_kwargs={"primaryjoin": "InterviewRoom.admin_id==User.id"})
    rooms_assigned: List["InterviewRoom"] = Relationship(back_populates="interviewer", sa_relationship_kwargs={"primaryjoin": "InterviewRoom.interviewer_id==User.id"})
    sessions: List["InterviewSession"] = Relationship(back_populates="candidate")
    question_banks: List["QuestionBank"] = Relationship(back_populates="admin")

class QuestionBank(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    admin_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    admin: User = Relationship(back_populates="question_banks")
    questions: List["QuestionGroup"] = Relationship(back_populates="bank")
    rooms: List["InterviewRoom"] = Relationship(back_populates="bank")

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

class InterviewRoom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_code: str = Field(unique=True, index=True)
    password: str
    admin_id: int = Field(foreign_key="user.id")
    interviewer_id: Optional[int] = Field(default=None, foreign_key="user.id")
    bank_id: Optional[int] = Field(default=None, foreign_key="questionbank.id")
    question_count: int = Field(default=5) # How many random questions to pick
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    max_sessions: Optional[int] = Field(default=None)
    
    admin: User = Relationship(back_populates="rooms_created", sa_relationship_kwargs={"primaryjoin": "InterviewRoom.admin_id==User.id"})
    interviewer: Optional[User] = Relationship(back_populates="rooms_assigned", sa_relationship_kwargs={"primaryjoin": "InterviewRoom.interviewer_id==User.id"})
    bank: Optional[QuestionBank] = Relationship(back_populates="rooms")
    sessions: List["InterviewSession"] = Relationship(back_populates="room")

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: Optional[int] = Field(default=None, foreign_key="interviewroom.id")
    candidate_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Legacy fields
    candidate_name: Optional[str] = None
    enrollment_audio_path: Optional[str] = None
    is_completed: bool = Field(default=False)
    
    # Shared/New fields
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_score: Optional[float] = None
    
    room: Optional["InterviewRoom"] = Relationship(back_populates="sessions")
    candidate: Optional["User"] = Relationship(back_populates="sessions")
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

# Rebuild models to resolve forward references
User.model_rebuild()
QuestionBank.model_rebuild()
QuestionGroup.model_rebuild()
InterviewRoom.model_rebuild()
InterviewSession.model_rebuild()
SessionQuestion.model_rebuild()
InterviewResponse.model_rebuild()
ProctoringEvent.model_rebuild()
