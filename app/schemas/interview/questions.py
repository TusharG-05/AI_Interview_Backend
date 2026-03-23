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
