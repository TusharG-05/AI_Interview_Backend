from typing import List, Optional
from pydantic import BaseModel

class HistoryItem(BaseModel):
    interview_id: int
    access_token: str
    paper_name: str
    date: str
    status: str
    score: Optional[float] = None
    duration_minutes: Optional[int] = None
    max_questions: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    warning_count: int = 0
    is_completed: bool = False
    current_status: Optional[str] = None
    allow_copy_paste: bool = False

    class Config:
        from_attributes = True

class GetHistoryResponse(BaseModel):
    sessions: List[HistoryItem]

    class Config:
        from_attributes = True

class UpcomingInterviewItem(BaseModel):
    id: int
    access_token: str
    paper_name: str
    schedule_time: str
    duration_minutes: int
    status: str

    class Config:
        from_attributes = True

class ListUpcomingInterviewsResponse(BaseModel):
    interviews: List[UpcomingInterviewItem]

    class Config:
        from_attributes = True
