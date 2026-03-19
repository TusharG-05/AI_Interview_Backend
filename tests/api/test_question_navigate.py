
import pytest
from app.models.db_models import InterviewSession, User, UserRole
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from sqlalchemy import select
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_allow_question_navigate_in_access_api(client, session, test_users):
    """
    Verify that allow_question_navigate is present in the access/{token} response.
    """
    admin, candidate, _ = test_users
    
    # Create a session with allow_question_navigate = True
    token = "test-navigate-token"
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        access_token=token,
        schedule_time=datetime.now(timezone.utc),
        allow_question_navigate=True,
        status="SCHEDULED"
    )
    session.add(interview)
    session.commit()
    
    # Get access using schedule-time endpoint (public, no auth required)
    response = client.get(f"/api/interview/schedule-time/{token}")
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert "allow_question_navigate" in data
    assert data["allow_question_navigate"] is True

    # Test with False (Default)
    token_false = "test-navigate-token-false"
    interview_false = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        access_token=token_false,
        schedule_time=datetime.now(timezone.utc),
        allow_question_navigate=False,
        status="SCHEDULED"
    )
    session.add(interview_false)
    session.commit()

    response = client.get(f"/api/interview/schedule-time/{token_false}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "allow_question_navigate" in data
    assert data["allow_question_navigate"] is False
