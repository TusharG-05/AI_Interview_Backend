import requests
import json
import uuid
import time
import os

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename):
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n% dummy content")

def test_api():
    print("Starting Comprehensive API Test...")
    
    # 1. AUTH: Login as Super Admin
    print("\n[1] Testing Auth Login (Super Admin)...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    assert login_res.status_code == 200, f"Super Admin Login failed: {login_res.status_code} - {login_res.text}"
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Super Admin Login Successful")
 
    # 2. AUTH: Me
    print("\n[2] Testing Auth Me...")
    me_res = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
    assert me_res.status_code == 200, f"Auth Me failed: {me_res.status_code} - {me_res.text}"
    print(f" Auth Me: {me_res.json()['data']['email']} ({me_res.json()['data']['role']})")

    # 3. DIRECT RESUME UPLOAD & USER CRUD
    print("\n[3] Testing Direct Resume Upload & User Management...")
    pdf_path = f"test_resume_{uuid.uuid4().hex[:6]}.pdf"
    create_test_pdf(pdf_path)
    
    cand_email = f"comp_cand_{uuid.uuid4().hex[:6]}@test.com"
    try:
        # Create User with Resume
        with open(pdf_path, "rb") as f:
            create_res = requests.post(
                f"{BASE_URL}/admin/users",
                headers=admin_headers,
                data={
                    "email": cand_email,
                    "full_name": "Comprehensive Candidate",
                    "password": "password123",
                    "role": "CANDIDATE"
                },
                files={"resume": ("initial_resume.pdf", f, "application/pdf")}
            )
        assert create_res.status_code == 201, f"User Creation with Resume failed: {create_res.text}"
        cand_data = create_res.json()["data"]
        candidate_id = cand_data["id"]
        assert cand_data["resume_url"] == f"/api/resume/{candidate_id}"
        print(f" User created with direct resume upload: ID {candidate_id}")

        # Update User (Replace Resume)
        with open(pdf_path, "rb") as f:
            patch_res = requests.patch(
                f"{BASE_URL}/admin/users/{candidate_id}",
                headers=admin_headers,
                data={"full_name": "Updated Comp Cand"},
                files={"resume": ("updated_resume.pdf", f, "application/pdf")}
            )
        assert patch_res.status_code == 200, f"User Update with Resume failed: {patch_res.text}"
        print(" User updated with resume replacement")

        # Verify Download
        get_resume = requests.get(f"{BASE_URL}/resume/", headers=admin_headers, params={"user_id": candidate_id})
        assert get_resume.status_code == 200
        assert get_resume.headers["content-type"] == "application/pdf"
        print(" Resume download verified via simplified GET API")

    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

    # 4. TEAMS: Create Team
    print("\n[4] Testing Team Creation...")
    team_name = f"UNIQUE_TEAM_{uuid.uuid4().hex}"
    team_res = requests.post(f"{BASE_URL}/super-admin/teams", headers=admin_headers, json={
        "name": team_name,
        "description": "Verification team"
    })
    assert team_res.status_code == 201, f"Team Creation failed: {team_res.text}"
    team_id = team_res.json()["data"]["id"]
    print(f" Team Created: {team_name} (ID: {team_id})")

    # 5. ADMIN: Create Paper
    print("\n[5] Testing Paper Creation...")
    paper_res = requests.post(f"{BASE_URL}/admin/papers", headers=admin_headers, json={
        "name": f"Test Paper {uuid.uuid4().hex[:6]}",
        "description": "Verification paper"
    })
    assert paper_res.status_code == 201, f"Paper Creation failed: {paper_res.text}"
    paper_id = paper_res.json()["data"]["id"]
    print(f" Paper Created: ID {paper_id}")

    # 6. ADMIN: Add Question
    print("\n[6] Testing Adding Question...")
    q_res = requests.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", headers=admin_headers, json={
        "content": "What is Python?",
        "topic": "Python",
        "difficulty": "Easy",
        "marks": 10,
        "response_type": "text"
    })
    assert q_res.status_code == 201, f"Adding Question failed: {q_res.text}"
    print(" Question Added Successfully")

    # 7. ADMIN: Schedule Interview
    print(f"\n[7] Testing Interview Scheduling...")
    print(f" Attempting to schedule with Paper ID: {paper_id}, Team ID: {team_id}, Cand ID: {candidate_id}")
    sched_res = requests.post(f"{BASE_URL}/admin/interviews/schedule", headers=admin_headers, json={
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_1",
        "schedule_time": "2026-03-20T15:00:00Z",
        "duration_minutes": 45
    })
    if sched_res.status_code != 201:
        print(f" ERROR: Schedule failed with status {sched_res.status_code}")
        print(f" Response: {sched_res.text}")
        # Try to fetch the paper to see if it's actually "missing"
        check_p = requests.get(f"{BASE_URL}/admin/papers/{paper_id}", headers=admin_headers)
        print(f" Diagnostic - Fetch Paper {paper_id} result: {check_p.status_code}")
        if check_p.status_code != 200:
            print(f" Diagnostic - Fetch Paper Response: {check_p.text}")
            
    assert sched_res.status_code == 201, f"Schedule failed: {sched_res.text}"
    interview_data = sched_res.json()["data"]["interview"]
    interview_id = interview_data["id"]
    access_token = sched_res.json()["data"]["access_token"]
    print(f" Interview Scheduled: ID {interview_id}")

    # 8. CANDIDATE: Login
    print("\n[8] Testing Candidate Login...")
    c_login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": cand_email,
        "password": "password123",
        "access_token": access_token
    })
    assert c_login_res.status_code == 200, f"Candidate Login failed: {c_login_res.text}"
    c_token = c_login_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}
    print(" Candidate Login Successful")

    # 9. INTERVIEW: Start & Submit
    print("\n[9] Testing Interview Workflow...")
    start_res = requests.post(f"{BASE_URL}/interview/start-session/{interview_id}", headers=c_headers)
    assert start_res.status_code == 200
    
    nq_res = requests.get(f"{BASE_URL}/interview/next-question/{interview_id}", headers=c_headers)
    assert nq_res.status_code == 200
    nq_data = nq_res.json()["data"]
    
    if nq_data.get("status") != "finished":
        q_id = nq_data["question_id"]
        sub_res = requests.post(f"{BASE_URL}/interview/submit-answer-text", headers=c_headers, data={
            "interview_id": interview_id,
            "question_id": q_id,
            "answer_text": "Python is a high-level programming language."
        })
        assert sub_res.status_code == 200
        print(" Answer Submitted Successfully")

    # 10. ADMIN: Results
    print("\n[10] Testing Admin Results...")
    res_res = requests.get(f"{BASE_URL}/admin/results/{interview_id}", headers=admin_headers)
    assert res_res.status_code == 200
    print(" Admin Results Verified")

    print("\nALL COMPREHENSIVE TESTS FINISHED!")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
