from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class AdminQuestionRead(BaseModel):
    id: int
    content: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str
    marks: int
    response_type: str

    class Config:
        from_attributes = True

class GetPaperResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    question_count: int = 0
    total_marks: int = 0
    questions: List[AdminQuestionRead] = []
    created_at: datetime

    class Config:
        from_attributes = True

class CreatePaperRequest(BaseModel):
    name: str
    description: str = ""
    admin_user: Optional[int] = None
    question_count: int = 0
    total_marks: int = 0

class QuestionCreateData(BaseModel):
    content: str = ""
    question_text: str = ""
    topic: str = "General"
    difficulty: str = "Medium"
    marks: int = 1
    response_type: str = "audio"

class CreatePaperWithQuestionsRequest(BaseModel):
    name: str
    description: str = ""
    questions: List[QuestionCreateData] = []
    total_marks: Optional[int] = None

class UpdatePaperRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
