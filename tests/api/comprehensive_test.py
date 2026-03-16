import requests
import json
import uuid
import time
import os

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename, content_suffix=""):
    # A more robust minimal 1-page PDF to satisfy Cloudinary's "auto" detection
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
        if create_res.status_code != 201:
            print(f" ERROR: User Creation failed: {create_res.text}")
        assert create_res.status_code == 201, f"User Creation with Resume failed: {create_res.text}"
        cand_data = create_res.json()["data"]
        candidate_id = cand_data["id"]
        # In the new Cloudinary logic, the resume_url is returned as /api/resume/{id} 
        # but internally it redirects.
        # Let's ensure resume_url is present.
        assert "resume_url" in cand_data
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
        get_resume = requests.get(f"{BASE_URL}/resume/", headers=admin_headers, params={"user_id": candidate_id}, allow_redirects=False)
        assert get_resume.status_code in [200, 307], f"Resume fetch failed. Code: {get_resume.status_code}, URL: {get_resume.url}, Headers: {get_resume.headers}"
        if get_resume.status_code == 307:
            print(f" Resume download verified via redirect: {get_resume.headers.get('location')}")
        else:
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

    # 11. ADMIN: Create Coding Paper
    print("\n[11] Testing Coding Paper Creation...")
    cp_res = requests.post(f"{BASE_URL}/admin/coding-papers/", headers=admin_headers, json={
        "name": f"Test Coding Paper {uuid.uuid4().hex[:6]}",
        "description": "Verification coding paper"
    })
    assert cp_res.status_code == 201, f"Coding Paper Creation failed: {cp_res.text}"
    coding_paper_id = cp_res.json()["data"]["id"]
    print(f" Coding Paper Created: ID {coding_paper_id}")

    # 12. ADMIN: Add Coding Question
    print("\n[12] Testing Adding Coding Question...")
    cq_res = requests.post(f"{BASE_URL}/admin/coding-papers/{coding_paper_id}/questions", headers=admin_headers, json={
        "title": "Two Sum",
        "problem_statement": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}],
        "constraints": ["2 <= nums.length <= 10^4"],
        "starter_code": "def twoSum(nums, target):\n    pass",
        "topic": "Arrays",
        "difficulty": "Easy",
        "marks": 10
    })
    assert cq_res.status_code == 201, f"Adding Coding Question failed: {cq_res.text}"
    coding_question_id = cq_res.json()["data"]["id"]
    print(f" Coding Question Added: ID {coding_question_id}")

    # 13. ADMIN: Schedule Coding Interview
    print(f"\n[13] Testing Coding Interview Scheduling...")
    c_sched_res = requests.post(f"{BASE_URL}/admin/interviews/schedule", headers=admin_headers, json={
        "candidate_id": candidate_id,
        "coding_paper_id": coding_paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_2",
        "schedule_time": "2026-03-21T15:00:00Z",
        "duration_minutes": 60
    })
    assert c_sched_res.status_code == 201, f"Coding Schedule failed: {c_sched_res.text}"
    c_interview_id = c_sched_res.json()["data"]["interview"]["id"]
    c_access_token = c_sched_res.json()["data"]["access_token"]
    print(f" Coding Interview Scheduled: ID {c_interview_id}")

    # 14. CANDIDATE: Login for Coding Interview
    print("\n[14] Testing Candidate Login (Coding)...")
    c2_login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": cand_email,
        "password": "password123",
        "access_token": c_access_token
    })
    assert c2_login_res.status_code == 200, f"Candidate Coding Login failed: {c2_login_res.text}"
    c2_token = c2_login_res.json()["data"]["access_token"]
    c2_headers = {"Authorization": f"Bearer {c2_token}"}
    print(" Candidate Coding Login Successful")

    # 15. INTERVIEW: Start & Submit Code
    print("\n[15] Testing Coding Interview Workflow...")
    c_start_res = requests.post(f"{BASE_URL}/interview/start-session/{c_interview_id}", headers=c2_headers)
    assert c_start_res.status_code == 200

    c_nq_res = requests.get(f"{BASE_URL}/interview/next-question/{c_interview_id}", headers=c2_headers)
    assert c_nq_res.status_code == 200
    c_nq_data = c_nq_res.json()["data"]
    print(f"DEBUG: Next question data: {c_nq_data}")

    if c_nq_data.get("status") != "finished":
        # 1. Capture coding question ID from response (proxy questions provide this)
        real_coding_q_id = c_nq_data.get("coding_question_id") or c_nq_data.get("coding_question")
        if real_coding_q_id is None:
            raise AssertionError(f"Missing coding_question_id in next-question response: {c_nq_data}")

        # 2. Define payload with standard ASCII spaces
        payload = {
            "interview_id": int(c_interview_id),
            "coding_question_id": int(real_coding_q_id),
            "answer_code": "def twoSum(nums, target):\n    return [0, 1]"
        }

        print(f" DEBUG: Sending Payload: {payload}")

        # 3. Post using 'data=' to send as form data
        c_sub_res = requests.post(
            f"{BASE_URL}/interview/submit-answer-code", 
            headers=c2_headers, 
            data=payload
        )

        assert c_sub_res.status_code == 200, f"Submit Answer Code failed: {c_sub_res.text}"
        print(" Code Answer Submitted Successfully")

    # 16. ADMIN: Results for Coding Interview
    print("\n[16] Testing Admin Results for Coding...")
    c_res_res = requests.get(f"{BASE_URL}/admin/results/{c_interview_id}", headers=admin_headers)
    assert c_res_res.status_code == 200
    print(" Admin Coding Results Verified")

    print("\nALL COMPREHENSIVE TESTS FINISHED!")
if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
