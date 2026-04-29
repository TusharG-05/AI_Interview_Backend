import pytest
from datetime import datetime, timedelta, timezone
from app.models.db_models import InterviewSession, InterviewStatus, CandidateStatus, InterviewRound

def test_access_interview_invalid_token(client, auth_headers):
    """Test 404 for invalid token"""
    response = client.get("/api/interview/access/invalid_token", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Invalid Interview Link"

def test_access_interview_cancelled(client, session, test_users, auth_headers):
    """Test 403 for cancelled interview"""
    admin, candidate, super_admin = test_users
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.CANCELLED,
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "Interview is cancelled"

def test_access_interview_completed(client, session, test_users, auth_headers):
    """Test 403 for completed interview"""
    admin, candidate, super_admin = test_users
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.COMPLETED,
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "This interview has already been completed."

def test_access_interview_expired_by_time(client, session, test_users, auth_headers):
    """Test 403 for expired interview (by time)"""
    admin, candidate, super_admin = test_users
    # Schedule far in the past
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc) - timedelta(hours=2),
        status=InterviewStatus.SCHEDULED,
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "This interview link has expired. Candidates must join within 30 minutes of the scheduled time."

def test_access_interview_suspended(client, session, test_users, auth_headers):
    """Test 403 for suspended interview"""
    admin, candidate, super_admin = test_users
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.SCHEDULED,
        is_suspended=True,
        suspension_reason="multiple_tab_switches",
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 403
    assert "suspended" in response.json()["message"].lower()
    assert "multiple_tab_switches" in response.json()["message"]

def test_access_interview_scheduled_future(client, session, test_users, auth_headers):
    """Test 200 for future scheduled interview (as requested)"""
    admin, candidate, super_admin = test_users
    # Schedule in the future
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc) + timedelta(hours=2),
        status=InterviewStatus.SCHEDULED,
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Interview not yet started. Please wait."
