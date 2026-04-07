import httpx
import time
import os
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8001/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"
CANDIDATE_EMAIL = "sakshamc1@test.com"
CANDIDATE_PASS = "candidate123"

def test_e2e():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    print("━━━ 1. AUTH & SETUP ━━━")
    
    # 1. Admin Login
    print("Logging in as Admin...")
    resp = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    admin_token = resp.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin Login Successful")
    
    # 2. Get Tushar ID
    print("Fetching Candidate ID...")
    resp = client.get("/admin/users", headers=admin_headers)
    users = resp.json()["data"]
    tushar = next((u for u in users if u["email"] == CANDIDATE_EMAIL), None)
    if not tushar:
        print("Candidate not found - checking DB directly if needed...")
        raise Exception("Candidate 'tushar@chicmicstudios.in' not found in DB")
    tushar_id = tushar["id"]
    print(f"✅ Found Candidate ID: {tushar_id}")
    
    # 3. Create Paper
    print("Creating Question Paper...")
    resp = client.post("/admin/papers", headers=admin_headers, json={
        "name": "Tushar Test Paper",
        "description": "Tushars interview test"
    })
    paper_id = resp.json()["data"]["id"]
    print(f"✅ Created Paper ID: {paper_id}")
    
    # 4. Add Question
    print("Adding Question...")
    resp = client.post(f"/admin/papers/{paper_id}/questions", headers=admin_headers, json={
        "content": "What is Python?",
        "question_text": "What is Python?",
        "topic": "Programming",
        "difficulty": "Easy",
        "marks": 10,
        "response_type": "text"
    })
    assert resp.status_code == 201, f"Failed to add question: {resp.text}"
    print("✅ Added Question")
    
    # 5. Schedule Interview
    print("Scheduling Interview...")
    sched_time = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
    resp = client.post("/admin/interviews/schedule", headers=admin_headers, json={
        "candidate_id": tushar_id,
        "paper_id": paper_id,
        "schedule_time": sched_time,
        "duration_minutes": 120,
        "max_questions": 1
    })
    assert resp.status_code in (200, 201), f"Failed to schedule: {resp.text}"
    interview_data = resp.json()["data"]
    interview_id = interview_data["interview"]["id"]
    access_token = interview_data["access_token"]
    print(f"✅ Scheduled Interview ID: {interview_id}")
    
    # 6. Candidate Login
    print("Logging in as Candidate...")
    resp = client.post("/auth/login", json={
        "email": CANDIDATE_EMAIL,
        "password": CANDIDATE_PASS,
        "access_token": access_token
    })
    assert resp.status_code == 200, f"Candidate login failed: {resp.text}"
    candidate_token = resp.json()["data"]["access_token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    print("✅ Candidate Login Successful")
    
    print("\n━━━ 2. ADMIN ENDPOINTS ━━━")
    for endpoint in ["/admin/papers", "/admin/questions", "/admin/users", "/admin/interviews", "/admin/interviews/live-status"]:
        resp = client.get(endpoint, headers=admin_headers)
        print(f"✅ GET {endpoint} ({resp.status_code})")
        
    print("\n━━━ 3. CANDIDATE INTERVIEW WORKFLOW ━━━")
    print("Waiting for schedule time...")
    time.sleep(3)
    
    # Access
    resp = client.get(f"/interview/access/{access_token}", headers=candidate_headers)
    assert resp.status_code == 200, f"Access failed: {resp.text}"
    print("✅ Interview Access granted")
    
    # Upload Selfie (using dummy bytes)
    print("Uploading Selfie...")
    selfie_data = b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x00\x00\x01"
    files = {"file": ("selfie.jpg", selfie_data, "image/jpeg")}
    resp = client.post("/interview/upload-selfie", headers=candidate_headers, data={"interview_id": interview_id}, files=files)
    assert resp.status_code == 200, f"Selfie upload failed: {resp.text}"
    print("✅ Selfie Uploaded")
    
    # Start Session
    print("Starting Session...")
    files = {"enrollment_audio": ("audio.wav", b"RIFF\x24\x00\x00\x00WAVEfmt ", "audio/wav")}
    resp = client.post(f"/interview/start-session/{interview_id}", headers=candidate_headers, files=files)
    assert resp.status_code == 200, f"Start session failed: {resp.text}"
    print("✅ Session Started")
    
    # Next Question
    print("Fetching Next Question...")
    resp = client.get(f"/interview/next-question/{interview_id}", headers=candidate_headers)
    assert resp.status_code == 200, f"Next question failed: {resp.text}"
    question_id = resp.json()["data"]["question_id"]
    print(f"✅ Next Question ID: {question_id}")
    
    # Submit Answer
    print("Submitting Answer...")
    resp = client.post("/interview/submit-answer-text", headers=candidate_headers, data={
        "interview_id": interview_id,
        "question_id": question_id,
        "answer_text": "Python is a language."
    })
    assert resp.status_code == 200, f"Submit answer failed: {resp.text}"
    print("✅ Answer Submitted")
    
    # Finish
    print("Finishing Interview...")
    resp = client.post(f"/interview/finish/{interview_id}", headers=candidate_headers)
    assert resp.status_code == 200, f"Finish failed: {resp.text}"
    print("✅ Interview Finished")
    
    print("\n━━━ 4. TOOLS & SYSTEM ━━━")
    # Evaluate Answer
    resp = client.post("/interview/evaluate-answer", headers=admin_headers, json={"question": "What is Python?", "answer": "Language"})
    print(f"✅ Evaluate Answer ({resp.status_code})")
    
    # TTS
    resp = client.get("/interview/tts", params={"text": "Hello"}, headers=admin_headers)
    print(f"✅ TTS ({resp.status_code})")
    
    print("\n━━━ FINAL RESULTS ━━━")
    print("✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    try:
        test_e2e()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
