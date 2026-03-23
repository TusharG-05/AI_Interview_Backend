from typing import List, Optional, Any
from pydantic import BaseModel, Field
from ..shared.user import UserNested
from datetime import datetime

class CodingQuestionFull(BaseModel):
    id: int
    paper_id: int
    title: str
    problem_statement: str
    examples: List[Any] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    topic: str
    difficulty: str
    marks: int

    class Config:
        from_attributes = True

class CodingPaperFull(BaseModel):
    id: int
    name: str
    description: str = ""
    question_count: int = 0
    total_marks: int = 0
    questions: List[CodingQuestionFull] = []
    created_at: datetime
    created_by: Optional[UserNested] = None

    class Config:
        from_attributes = True

class GenerateCodingPaperRequest(BaseModel):
    ai_prompt: str = Field(..., min_length=3)
    difficulty_mix: str = "mixed"
    num_questions: int = Field(..., ge=1, le=20)
    paper_name: Optional[str] = None

class CodingPaperCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None

class CodingPaperUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CodingQuestionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    problem_statement: str = Field(..., min_length=10)
    examples: List[dict] = []
    constraints: List[str] = []
    starter_code: Optional[str] = None
    topic: str = "Algorithms"
    difficulty: str = "Medium"
    marks: int = 6

class CodingQuestionUpdateRequest(BaseModel):
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    examples: Optional[List[dict]] = None
    constraints: Optional[List[str]] = None
    starter_code: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None
