import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.models.db_models import InterviewSession, QuestionPaper, InterviewStatus, CandidateStatus

def test_tab_switch_policy_scenarios(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users
    
    # 1. Setup
    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()
    
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60,
        status=InterviewStatus.LIVE,
        current_status=CandidateStatus.INTERVIEW_ACTIVE
    )
    session.add(interview)
    session.commit()
    
    interview_id = interview.id
    
    # Scenario 1: TAB_SWITCH -> TAB_RETURN within 30 seconds
    response = client.post(
        f"/api/interview/{interview_id}/tab-switch",
        json={"event_type": "TAB_SWITCH"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["tab_switch_count"] == 1
    assert response.json()["data"]["tab_warning_active"] is True
    
    response = client.post(
        f"/api/interview/{interview_id}/tab-switch",
        json={"event_type": "TAB_RETURN"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["tab_warning_active"] is False
    assert response.json()["data"]["is_suspended"] is False
    
    # Scenario 2: TAB_SWITCH -> return after 30 seconds (Manual return)
    # Re-switch (Warning 2)
    client.post(
        f"/api/interview/{interview_id}/tab-switch",
        json={"event_type": "TAB_SWITCH"},
        headers=auth_headers
    )
    
    # Mock time jump
    future_time = datetime.now(timezone.utc) + timedelta(seconds=40)
    with patch("app.routers.interview.datetime") as mock_datetime:
        mock_datetime.now.return_value = future_time
        # Return event should terminate
        response = client.post(
            f"/api/interview/{interview_id}/tab-switch",
            json={"event_type": "TAB_RETURN"},
            headers=auth_headers
        )
        assert response.status_code == 403
        data = response.json()["data"]
        assert data["reason"] == "tab_switch_timeout"
        assert data["is_suspended"] is True

    # Scenario 5: Try submitting work after termination
    response = client.get(
        f"/api/interview/next-question/{interview_id}",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "terminated" in response.json()["message"]

def test_third_tab_switch_immediate_termination(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users
    
    # 1. Setup
    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()
    
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60,
        status=InterviewStatus.LIVE,
        current_status=CandidateStatus.INTERVIEW_ACTIVE,
        tab_switch_count=2 # Already had 2 switches
    )
    session.add(interview)
    session.commit()
    
    interview_id = interview.id
    
    # 3rd switch
    response = client.post(
        f"/api/interview/{interview_id}/tab-switch",
        json={"event_type": "TAB_SWITCH"},
        headers=auth_headers
    )
    assert response.status_code == 403
    data = response.json()["data"]
    assert data["reason"] == "multiple_tab_switch"
    assert data["is_suspended"] is True

def test_proactive_timeout_on_api_call(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users
    
    # 1. Setup
    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()
    
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60,
        status=InterviewStatus.LIVE,
        current_status=CandidateStatus.INTERVIEW_ACTIVE,
        tab_warning_active=True,
        tab_switch_timestamp=datetime.now(timezone.utc) - timedelta(seconds=50)
    )
    session.add(interview)
    session.commit()
    
    interview_id = interview.id
    
    # Proactive check on next-question
    response = client.get(
        f"/api/interview/next-question/{interview_id}",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "terminated" in response.json()["message"]
    
    session.refresh(interview)
    assert interview.is_suspended is True
    assert interview.suspension_reason == "tab_switch_timeout"
