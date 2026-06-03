from typing import Optional
from pydantic import BaseModel

class NextQuestionResponse(BaseModel):
    id: int
    paper_id: Optional[int] = None
    content: str
    paper_name: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None
    response_type: str = "audio"

    class Config:
        from_attributes = True

class CodingQuestionBasic(BaseModel):
    id: int
    title: str
    problem_statement: str
    difficulty: str
    marks: int

    class Config:
        from_attributes = True

class AnswerRequest(BaseModel):
    question: str
    answer: str
    question_id: Optional[int] = None          # Standard Questions table ID
    coding_question_id: Optional[int] = None   # CodingQuestions table ID
    question_marks: Optional[float] = None     # Fallback: caller can pass marks directly

class QuestionStartRequest(BaseModel):
    sessionId: int
    questionId: Optional[int] = None
