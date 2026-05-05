from typing import Optional, Literal, Any, Dict
from pydantic import BaseModel
from datetime import datetime


class WebSocketEvent(BaseModel):
    """Base WebSocket event structure"""
    event_type: str
    interview_id: int
    data: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== VIOLATION EVENTS ==========

class ViolationEvent(BaseModel):
    """
    Violation event sent to both candidate and admin dashboard.
    
    Maps violation_type:
    - tab_switch
    - multiple_faces
    - no_face
    - wrong_candidate
    """
    event_type: str = "violation"
    interview_id: int
    violation_type: str  # 'tab_switch', 'multiple_faces', 'no_face', 'wrong_candidate'
    details: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

    class Config:
        from_attributes = True


# ========== ADMIN DASHBOARD EVENTS ==========

class AdminDashboardEvent(BaseModel):
    """
    Admin dashboard event for major interview lifecycle changes.
    
    Event types:
    - interview_started: Interview transitioned to LIVE
    - interview_suspended: Violation threshold exceeded
    - interview_completed: Interview finished with result
    - interview_expired: Interview time expired
    """
    event_type: Literal["interview_started", "interview_suspended", "interview_completed", "interview_expired"]
    interview_id: int
    data: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None

    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

    class Config:
        from_attributes = True


# ========== BACKWARD COMPATIBILITY TYPES ==========

class InterviewStartedEvent(BaseModel):
    """Legacy: Use AdminDashboardEvent with event_type='interview_started'"""
    event_type: Literal["interview_started"] = "interview_started"
    interview_id: int
    data: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class ViolationDetectedEvent(BaseModel):
    """Legacy: Use ViolationEvent"""
    event_type: Literal["violation_detected"] = "violation_detected"
    interview_id: int
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class InterviewSuspendedEvent(BaseModel):
    """Legacy: Use AdminDashboardEvent with event_type='interview_suspended'"""
    event_type: Literal["interview_suspended"] = "interview_suspended"
    interview_id: int
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class InterviewCompletedEvent(BaseModel):
    """Legacy: Use AdminDashboardEvent with event_type='interview_completed'"""
    event_type: Literal["interview_completed"] = "interview_completed"
    interview_id: int
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class InterviewExpiredEvent(BaseModel):
    """Legacy: Use AdminDashboardEvent with event_type='interview_expired'"""
    event_type: Literal["interview_expired"] = "interview_expired"
    interview_id: int
    data: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class CandidateViolationEvent(BaseModel):
    """Legacy: Use ViolationEvent"""
    event_type: str
    violation_count: Optional[int] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminDashboardResponse(BaseModel):
    """Standardized response for admin dashboard WebSocket"""
    event_type: str
    interview_id: int
    data: Dict[str, Any]

class DashboardData(BaseModel):
    """Aggregated dashboard metrics included in admin websocket payloads."""
    live: int
    proctoring_activity: str  # percentage string, e.g. "12.34%"
    failed_today: int
    passed_today: int

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

