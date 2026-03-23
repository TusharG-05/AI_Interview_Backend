from typing import Optional
from pydantic import BaseModel, model_validator
from .dashboard import AdminInterviewSessionDetail
from ..shared.user import UserNested

class ScheduleInterviewRequest(BaseModel):
    candidate_id: int
    team_id: Optional[int] = None
    paper_id: Optional[int] = None
    coding_paper_id: Optional[int] = None
    interview_round: str
    schedule_time: str # ISO format
    duration_minutes: int = 1440
    max_questions: Optional[int] = None
    allow_copy_paste: bool = False
    allow_question_navigate: bool = False

    @model_validator(mode="after")
    def at_least_one_paper(self) -> "ScheduleInterviewRequest":
        if self.paper_id is None and self.coding_paper_id is None:
            raise ValueError("At least one paper_id or coding_paper_id must be provided.")
        return self

class UpdateInterviewRequest(BaseModel):
    schedule_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    paper_id: Optional[int] = None
    coding_paper_id: Optional[int] = None
    max_questions: Optional[int] = None
    allow_copy_paste: Optional[bool] = None
    allow_question_navigate: Optional[bool] = None

class InterviewLinkResponse(BaseModel):
    interview: AdminInterviewSessionDetail
    admin_user: UserNested
    candidate_user: UserNested
    access_token: str
    link: str
    scheduled_at: str
    warning: Optional[str] = None

    class Config:
        from_attributes = True
