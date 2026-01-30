from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    CANDIDATE = "candidate"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: UserRole = Field(default=UserRole.CANDIDATE)
    resume_text: Optional[str] = Field(default=None)  # Stored extracted text
    profile_image: Optional[str] = Field(default=None) # Path to uploaded selfie
    
    rooms_created: List["InterviewRoom"] = Relationship(back_populates="admin")
    sessions: List["InterviewSession"] = Relationship(back_populates="candidate")

class InterviewRoom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_code: str = Field(unique=True, index=True)
    password: str
    admin_id: int = Field(foreign_key="user.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    max_sessions: Optional[int] = Field(default=None)
    
    admin: User = Relationship(back_populates="rooms_created")
    sessions: List["InterviewSession"] = Relationship(back_populates="room")

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: Optional[str] = None
    question_text: Optional[str] = None # Legacy support
    topic: Optional[str] = None
    difficulty: str = Field(default="Medium")
    reference_answer: Optional[str] = None # Legacy support
    
    responses: List["InterviewResponse"] = Relationship(back_populates="question")

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
    question_id: int = Field(foreign_key="question.id")
    
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
    question: Question = Relationship(back_populates="responses")

# Aliases for legacy code
CandidateResponse = InterviewResponse

# Rebuild models to resolve forward references
User.model_rebuild()
InterviewRoom.model_rebuild()
InterviewSession.model_rebuild()
Question.model_rebuild()
InterviewResponse.model_rebuild()
ProctoringEvent.model_rebuild()

