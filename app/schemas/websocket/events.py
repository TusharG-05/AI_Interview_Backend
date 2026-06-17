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

# ========== ADMIN DASHBOARD EVENTS ==========

class AdminDashboardEvent(BaseModel):
    """
    Admin dashboard event for major interview lifecycle changes and proctoring violations.
    
    Event types:
    - Interview_login
    - Interview_started
    - Interview_disconnected
    - Interview_finished
    - Interview_suspended
    - Proctoring_violation
    """
    event_type: Literal[
        "Initial_dashboard_data",
        "Interview_login", 
        "Interview_started", 
        "Interview_disconnected",
        "Interview_finished", 
        "Interview_suspended", 
        "Interview_expired",
        "Proctoring_violation"
    ]
    interview_id: int
    data: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None

    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

    class Config:
        from_attributes = True

class AdminDashboardResponse(BaseModel):
    """Standardized response for admin dashboard WebSocket"""
    event_type: str
    interview_id: int
    data: Dict[str, Any]

class DashboardData(BaseModel):
    """Aggregated dashboard metrics included in admin websocket payloads."""
    today_total_interviews: int
    live: int
    proctoring_activity: str  # percentage string, e.g. "12.34%"
    failed_today: int
    passed_today: int

    class Config:
        from_attributes = True
