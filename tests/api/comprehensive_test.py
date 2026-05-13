import uuid
import os
from datetime import datetime, timezone, timedelta
from app.models.db_models import UserRole, InterviewStatus

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename, content_suffix=""):
    # A more robust minimal 1-page PDF for testing
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type/Pages/Kids [3 0 R]/Count 1>> endobj\n"
        b"3 0 obj <</Type/Page/Parent 2 0 R/MediaBox [0 0 612 792]/Resources<<>>/Contents 4 0 R>> endobj\n"
        b"4 0 obj <</Length 60>> stream\n"
        b"BT /F1 24 Tf 100 100 Td (Minimal PDF for Cloudinary Test " + content_suffix.encode() + b") Tj ET\n"
        b"endstream endobj\n"
        b"trailer <</Size 5/Root 1 0 R>>\n"
        b"%%EOF"
    )
    with open(filename, "wb") as f:
        f.write(pdf_content)

def test_comprehensive_workflow(client, session, test_users, auth_headers, super_auth_headers):
    """
    Complete end-to-end workflow:
    1. Admin creates Paper & Team
    2. Admin schedules Interview
    3. Candidate logins and starts session
    4. Candidate submits answer
    5. Admin verifies results
    6. Admin adds coding interview components
    7. Candidate performs coding interview
    """
    admin, candidate, super_admin = test_users
    
    # 1. ADMIN: Setup
    paper_res = client.post("/api/admin/papers", json={"name": "Comp-Test Paper"}, headers=auth_headers)
    assert paper_res.status_code == 201
    paper_id = paper_res.json()["data"]["id"]
    
    team_name = f"Comp-Team-{uuid.uuid4().hex[:6]}"
    team_res = client.post("/api/super-admin/teams", json={"name": team_name}, headers=super_auth_headers)
    assert team_res.status_code == 201
    team_id = team_res.json()["data"]["id"]

    q_res = client.post(f"/api/admin/papers/{paper_id}/questions", json={
        "content": "What is Python?",
        "topic": "General",
        "difficulty": "Easy",
        "marks": 10,
        "response_type": "text"
    }, headers=auth_headers)
    assert q_res.status_code == 201, f"Adding Question failed: {q_res.text}"
    q_id = q_res.json()["data"]["id"]
    print(f" Question Added: ID {q_id}")

    # 2. ADMIN: Schedule Standard Interview
    sched_res = client.post("/api/admin/interviews/schedule", json={
        "candidate_id": candidate.id,
        "paper_id": paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_1",
        "schedule_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "duration_minutes": 60
    }, headers=auth_headers)
    assert sched_res.status_code == 201, f"Scheduling failed: {sched_res.text}"
    interview_id = sched_res.json()["data"]["interview"]["id"]
    access_token = sched_res.json()["data"]["access_token"]

    # 3. CANDIDATE: Access & Start
    # Login
    login_res = client.post("/api/auth/login", json={
        "email": candidate.email,
        "password": "TestPass123!", 
        "access_token": access_token
    })
    assert login_res.status_code == 200, f"Candidate Login failed: {login_res.text}"
    cand_token = login_res.json()["data"]["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    
    start_res = client.post(f"/api/interview/start-session/{interview_id}", headers=cand_headers)
    assert start_res.status_code == 200, f"Session Start failed: {start_res.text}"
    print(" Candidate Login and Session Started")

    # 9. CANDIDATE: Submit Answer
    print("\n[9] Testing Submitting Answer...")
    sub_res = client.post(f"/api/interview/submit-answer-text", headers=cand_headers, data={
        "interview_id": interview_id,
        "question_id": q_id,
        "answer_text": "Python is a programming language."
    })
    assert sub_res.status_code == 200, f"Submitting Answer failed: {sub_res.text}"
    print(" Answer Submitted Successfully")

    # 5. ADMIN: Verify Result
    res_res = client.get(f"/api/admin/results/{interview_id}", headers=auth_headers)
    assert res_res.status_code == 200
    print("Standard Workflow Verified")

    # 6. ADMIN: Create Coding Paper & Question
    cp_res = client.post("/api/admin/coding-papers/", json={
        "name": "Comp-Test Coding Paper",
        "description": "Verification coding paper"
    }, headers=auth_headers)
    assert cp_res.status_code == 201
    coding_paper_id = cp_res.json()["data"]["id"]

    cq_res = client.post(f"/api/admin/coding-papers/{coding_paper_id}/questions", json={
        "title": "Two Sum",
        "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}],
        "constraints": ["2 <= nums.length <= 10^4"],
        "starter_code": "def twoSum(nums, target):\n    pass",
        "topic": "Arrays",
        "difficulty": "Easy",
        "marks": 10
    }, headers=auth_headers)
    assert cq_res.status_code == 201
    coding_question_id = cq_res.json()["data"]["id"]

    # 7. ADMIN: Schedule Coding Interview
    c_sched_res = client.post("/api/admin/interviews/schedule", json={
        "candidate_id": candidate.id,
        "coding_paper_id": coding_paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_2",
        "schedule_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "duration_minutes": 60
    }, headers=auth_headers)
    assert c_sched_res.status_code == 201
    c_interview_id = c_sched_res.json()["data"]["interview"]["id"]
    c_access_token = c_sched_res.json()["data"]["access_token"]

    # 8. CANDIDATE: Login & Perform Coding Interview
    c2_login_res = client.post("/api/auth/login", json={
        "email": candidate.email,
        "password": "TestPass123!",
        "access_token": c_access_token
    })
    assert c2_login_res.status_code == 200
    c2_token = c2_login_res.json()["data"]["access_token"]
    c2_headers = {"Authorization": f"Bearer {c2_token}"}

    c_start_res = client.post(f"/api/interview/start-session/{c_interview_id}", headers=c2_headers)
    assert c_start_res.status_code == 200

    c_nq_res = client.get(f"/api/interview/next-question/{c_interview_id}", headers=c2_headers)
    assert c_nq_res.status_code == 200
    c_nq_data = c_nq_res.json()["data"]

    if c_nq_data.get("status") != "finished":
        real_coding_q_id = c_nq_data.get("coding_question_id") or c_nq_data.get("coding_question")
        assert real_coding_q_id is not None

        c_sub_res = client.post("/api/interview/submit-answer-code", headers=c2_headers, data={
            "interview_id": c_interview_id,
            "coding_question_id": real_coding_q_id,
            "answer_code": "def twoSum(nums, target):\n    return [0, 1]"
        })
        assert c_sub_res.status_code == 200

    # 9. ADMIN: Verify Coding Results
    c_res_res = client.get(f"/api/admin/results/{c_interview_id}", headers=auth_headers)
    assert c_res_res.status_code == 200
    print("Coding Workflow Verified")
