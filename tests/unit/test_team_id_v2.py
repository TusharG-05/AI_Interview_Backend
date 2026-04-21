import pytest
from datetime import datetime, timezone
from app.models.db_models import User, UserRole, QuestionPaper, InterviewSession, InterviewResult, InterviewStatus, Team
from app.auth.security import get_password_hash, create_access_token

def test_team_id_in_responses(session, client):
    # 1. Setup Data
    # Create a real Team first to satisfy foreign key constraints
    test_team = Team(name="Test Team", description="Verification Team")
    session.add(test_team)
    session.commit()
    session.refresh(test_team)
    
    TEST_TEAM_ID = test_team.id
    
    # Admin
    admin = User(
        email="admin_team@test.com", 
        full_name="Admin Team", 
        password_hash=get_password_hash("test"), 
        role=UserRole.ADMIN,
        team_id=TEST_TEAM_ID
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    admin_token = create_access_token(data={"sub": admin.email})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Candidate
    candidate = User(
        email="cand_team@test.com", 
        full_name="Candidate Team", 
        password_hash=get_password_hash("test"), 
        role=UserRole.CANDIDATE,
        team_id=TEST_TEAM_ID
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    
    cand_token = create_access_token(data={"sub": candidate.email})
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    
    # Paper
    paper = QuestionPaper(name="Team Paper", admin_user=admin.id)
    session.add(paper)
    session.commit()
    session.refresh(paper)
    
    # Interview
    interview = InterviewSession(
        admin_id=admin.id, 
        candidate_id=candidate.id, 
        paper_id=paper.id, 
        schedule_time=datetime.now(timezone.utc), 
        duration_minutes=60, 
        status=InterviewStatus.SCHEDULED,
        access_token="test-token-123",
        team_id=TEST_TEAM_ID
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # Result
    result = InterviewResult(interview_id=interview.id)
    session.add(result)
    session.commit()
    
    # 2. Test /auth/me
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    r_data = response.json()["data"]
    assert r_data["team"]["id"] == TEST_TEAM_ID
    print("✓ /auth/me has team info")
    
    # 3. Test /interview/access/{token}
    # Provide candidate headers because the endpoint requires login
    response = client.get(f"/api/interview/access/{interview.access_token}", headers=cand_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["candidate_user"]["team"]["id"] == TEST_TEAM_ID
    assert data["admin_user"]["team"]["id"] == TEST_TEAM_ID
    print("✓ /interview/access has team info")
    
    # 4. Test /admin/results/{interview_id}
    response = client.get(f"/api/admin/results/{interview.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    # Check if team is in candidate_user directly
    assert data["candidate_user"]["team"]["id"] == TEST_TEAM_ID
    assert data["admin_user"]["team"]["id"] == TEST_TEAM_ID
    print("✓ /admin/results has team info")

    # 5. Test /admin/interviews/{interview_id}
    response = client.get(f"/api/admin/interviews/{interview.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    # Usually interviews endpoint returns data wrapped in "interview" OR direct?
    # Let's check admin router for /interviews/{id}
    if "interview" in data:
        assert data["interview"]["candidate_user"]["team"]["id"] == TEST_TEAM_ID
    else:
        assert data["candidate_user"]["team"]["id"] == TEST_TEAM_ID
    print("✓ /admin/interviews/{id} has team info")
