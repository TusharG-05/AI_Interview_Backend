
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.db_models import UserRole, InterviewStatus

def test_comprehensive_workflow(client, session, test_users, auth_headers, super_auth_headers):
    """
    Complete end-to-end workflow:
    1. Admin creates Paper & Team
    2. Admin schedules Interview
    3. Candidate logins and starts session
    4. Candidate submits answer
    5. Admin verifies results
    """
    admin, candidate, super_admin = test_users
    
    # 1. ADMIN: Setup
    paper_res = client.post("/api/admin/papers", json={"name": "Comp-Test Paper"}, headers=auth_headers)
    assert paper_res.status_code == 201
    paper_id = paper_res.json()["data"]["id"]
    
    team_res = client.post("/api/super-admin/teams", json={"name": f"Comp-Team-{uuid.uuid4().hex[:6]}"}, headers=super_auth_headers)
    assert team_res.status_code == 201
    team_id = team_res.json()["data"]["id"]

    q_res = client.post(f"/api/admin/papers/{paper_id}/questions", json={
        "content": "What is Python?",
        "topic": "General",
        "difficulty": "Easy",
        "marks": 10,
        "response_type": "text"
    }, headers=auth_headers)
    assert q_res.status_code == 201
    q_id = q_res.json()["data"]["id"]

    # 2. ADMIN: Schedule
    sched_res = client.post("/api/admin/interviews/schedule", json={
        "candidate_id": candidate.id,
        "paper_id": paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_1",
        "schedule_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "duration_minutes": 60
    }, headers=auth_headers)
    assert sched_res.status_code == 201
    interview_id = sched_res.json()["data"]["interview"]["id"]
    access_token = sched_res.json()["data"]["access_token"]

    # 3. CANDIDATE: Access & Start
    # Public check
    pub_res = client.get(f"/api/interview/schedule-time/{access_token}")
    assert pub_res.status_code == 200

    # Login
    login_res = client.post("/api/auth/login", json={
        "email": candidate.email,
        "password": "TestPass123!", # From test_users fixture setup logic
        "access_token": access_token
    })
    assert login_res.status_code == 200
    c_token = login_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # Start
    start_res = client.post(f"/api/interview/start-session/{interview_id}", headers=c_headers)
    assert start_res.status_code == 200

    # 4. CANDIDATE: Workflow
    nq_res = client.get(f"/api/interview/next-question/{interview_id}", headers=c_headers)
    assert nq_res.status_code == 200
    
    sub_res = client.post("/api/interview/submit-answer-text", data={
        "interview_id": interview_id,
        "question_id": q_id,
        "answer_text": "Python is a versatile language."
    }, headers=c_headers)
    assert sub_res.status_code == 200

    # 5. ADMIN: Verify Result
    res_res = client.get(f"/api/admin/results/{interview_id}", headers=auth_headers)
    assert res_res.status_code == 200
    print("Comprehensive Workflow Verified")
