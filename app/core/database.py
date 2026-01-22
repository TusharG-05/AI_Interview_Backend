import os
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database path (relative to the project root)
DB_PATH = "sqlite:///./interview_system.db"

Base = declarative_base()

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String, nullable=True)
    enrollment_audio_path = Column(String, nullable=True)  # New field for voice print
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    responses = relationship("CandidateResponse", back_populates="session")

class CandidateResponse(Base):
    __tablename__ = "candidate_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    audio_path = Column(String, nullable=True)  # Path to saved .wav file
    transcribed_text = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)
    
    session = relationship("InterviewSession", back_populates="responses")
    question = relationship("Question")

from sqlalchemy import create_engine
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
