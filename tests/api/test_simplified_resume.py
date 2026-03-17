
import pytest
import io
import uuid
from app.models.db_models import UserRole, InterviewSession, QuestionPaper, InterviewStatus
from datetime import datetime, timezone, timedelta

def test_simplified_resume_workflow(client, session, test_users, auth_headers):
    """
    Test resume access control:
    - Candidate can access their own
    - Candidate cannot access others
    - Admin can access any
    """
    admin, candidate, super_admin = test_users
    
    # 1. SETUP: Create interview session for candidate to get access_token
    paper = QuestionPaper(name="Resume Test Paper", admin_user=admin.id)
    session.add(paper)
    session.commit()
    
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc) + timedelta(hours=1),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # 2. SETUP: Upload Resume for Candidate via Admin Patch
    resume_content = b"%PDF-1.4\nSimple Resume"
    patch_res = client.patch(
        f"/api/admin/users/{candidate.id}",
        headers=auth_headers,
        files={"resume": ("simple.pdf", io.BytesIO(resume_content), "application/pdf")}
    )
    assert patch_res.status_code == 200

    # 3. CANDIDATE ACCESS
    # Login candidate with access_token
    login_res = client.post("/api/auth/login", json={
        "email": candidate.email,
        "password": "TestPass123!",
        "access_token": interview.access_token
    })
    assert login_res.status_code == 200
    c_token = login_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # Own resume (No ID param)
    get_self = client.get("/api/resume/", headers=c_headers)
    assert get_self.status_code == 200
    
    # Own resume (With ID param)
    get_self_id = client.get("/api/resume/", headers=c_headers, params={"user_id": candidate.id})
    assert get_self_id.status_code == 200

    # Other resume (Forbidden)
    get_other = client.get("/api/resume/", headers=c_headers, params={"user_id": admin.id})
    assert get_other.status_code == 403

    # 4. ADMIN ACCESS
    get_cand_as_admin = client.get("/api/resume/", headers=auth_headers, params={"user_id": candidate.id})
    assert get_cand_as_admin.status_code == 200
