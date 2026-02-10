from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import DATABASE_URL

# Configure connection args based on database type
engine_args = {}
connect_args = {}

if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    engine_args = {"pool_pre_ping": True}

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_args)

def init_db():
    from ..models.db_models import (
        User, QuestionPaper, Questions, 
        InterviewSession, InterviewResponse,
        SessionQuestion, ProctoringEvent
    )
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
