
import pytest
from app.models.db_models import UserRole, InterviewStatus, InterviewSession
from datetime import datetime, timezone, timedelta

def test_candidate_history(client, session, test_users):
    """Test candidate can view their interview history."""
    admin, candidate, super_admin = test_users
    
    # Setup prerequisite objects
    from app.models.db_models import QuestionPaper, Team
    paper = QuestionPaper(name="History Paper", admin_user=admin.id)
    team = Team(name="History Team")
    session.add(paper)
    session.add(team)
    session.commit()
    
    # Setup some interviews
    i1 = InterviewSession(
        admin_id=admin.id, 
        candidate_id=candidate.id, 
        paper_id=paper.id, 
        team_id=team.id,
        status=InterviewStatus.COMPLETED,
        schedule_time=datetime.now(timezone.utc) - timedelta(days=1),
        duration_minutes=60
    )
    session.add(i1)
    session.commit()
    
    # Auth as candidate
    from app.auth.security import create_access_token
    token = create_access_token(data={"sub": candidate.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/candidate/history", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1

def test_public_schedule_time(client, session, test_users):
    """Test public access to schedule time via token."""
    admin, candidate, super_admin = test_users
    
    # Setup prerequisite objects
    from app.models.db_models import QuestionPaper, Team
    paper = QuestionPaper(name="Schedule Paper", admin_user=admin.id)
    team = Team(name="Schedule Team")
    session.add(paper)
    session.add(team)
    session.commit()
    
    # Create interview with token
    token_val = "secret-access-token-123"
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        team_id=team.id,
        access_token=token_val,
        status=InterviewStatus.SCHEDULED,
        schedule_time=datetime.now(timezone.utc) + timedelta(hours=2),
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    
    # 1. Valid Access
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    
    # 2. Invalid Token
    response = client.get("/api/interview/schedule-time/wrong-token")
    assert response.status_code == 404
    
    # 3. Cancelled Interview
    interview.status = InterviewStatus.CANCELLED
    session.add(interview)
    session.commit()
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 403
    assert "cancelled" in response.json()["message"].lower()

def test_candidate_me_endpoint(client, test_users):
    """Test the /auth/me endpoint for a candidate."""
    admin, candidate, super_admin = test_users
    from app.auth.security import create_access_token
    token = create_access_token(data={"sub": candidate.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["role"] == UserRole.CANDIDATE.value
