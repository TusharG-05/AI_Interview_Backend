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
    content: str
    topic: str
    difficulty: str = Field(default="Medium")
    
    responses: List["InterviewResponse"] = Relationship(back_populates="question")

class InterviewSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="interviewroom.id")
    candidate_id: int = Field(foreign_key="user.id")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_score: Optional[float] = None
    
    room: InterviewRoom = Relationship(back_populates="sessions")
    candidate: User = Relationship(back_populates="sessions")
    responses: List["InterviewResponse"] = Relationship(back_populates="session")

class InterviewResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interviewsession.id")
    question_id: int = Field(foreign_key="question.id")
    answer_text: str
    evaluation_text: str
    score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    session: InterviewSession = Relationship(back_populates="responses")
    question: Question = Relationship(back_populates="responses")

# Rebuild models to resolve forward references
User.model_rebuild()
InterviewRoom.model_rebuild()
InterviewSession.model_rebuild()
Question.model_rebuild()
InterviewResponse.model_rebuild()
