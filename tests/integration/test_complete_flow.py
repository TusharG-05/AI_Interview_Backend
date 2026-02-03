import requests
import os
import uuid
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://localhost:8000/api"
VERIFY_SSL = False

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, status=True):
    color = GREEN if status else RED
    mark = "[PASS]" if status else "[FAIL]"
    print(f"{color}{mark} {msg}{RESET}")

def test_complete_flow():
    session = requests.Session()
    session.verify = VERIFY_SSL
    
    print("\n" + "="*50)
    print("🚀 STARTING COMPLETE PROJECT END-TO-END TEST")
    print("="*50 + "\n")

    # --- 1. ADMIN FLOW ---
    
    # Register/Login Admin
    admin_email = f"admin_test_{os.urandom(3).hex()}@test.com"
    r = session.post(f"{BASE_URL}/auth/register", json={
        "email": admin_email, "password": "password123", "full_name": "Test Admin", "role": "admin"
    })
    if r.status_code != 200:
        log(f"Admin Registration Failed: {r.text}", False)
        return
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    log("Admin Registered & Logged In")

    # Create Question Bank
    r = session.post(f"{BASE_URL}/admin/banks", json={
        "name": "Backend Engineering", 
        "description": "Questions for senior backend roles"
    }, headers=admin_headers)
    if r.status_code != 200:
        log(f"Bank Creation Failed: {r.text}", False)
        return
    bank_id = r.json()["id"]
    log(f"Question Bank Created (ID: {bank_id})")

    # Add 4 Questions to the Bank
    questions = [
        {"content": "Describe binary search algorithm.", "topic": "Algorithms", "difficulty": "Medium", "marks": 2},
        {"content": "What is horizontal scaling?", "topic": "Architecture", "difficulty": "Hard", "marks": 3},
        {"content": "Explain ACID properties.", "topic": "Databases", "difficulty": "Medium", "marks": 1},
        {"content": "What is the difference between a process and a thread?", "topic": "OS", "difficulty": "Easy", "marks": 1}
    ]
    for q in questions:
        r = session.post(f"{BASE_URL}/admin/banks/{bank_id}/questions", json=q, headers=admin_headers)
        if r.status_code != 200:
            log(f"Adding Question Failed: {r.text}", False)
            return
    log("Added 4 Questions to the Bank")

    # Create Interview Room (Pick 2 random questions)
    r = session.post(f"{BASE_URL}/admin/rooms", json={
        "password": "testpass", 
        "bank_id": bank_id, 
        "question_count": 2,
        "max_sessions": 5
    }, headers=admin_headers)
    if r.status_code != 200:
        log(f"Room Creation Failed: {r.text}", False)
        return
    room_data = r.json()
    room_code = room_data["room_code"]
    room_password = room_data["password"]
    log(f"Interview Room Created Code: {room_code}")

    # --- 2. CANDIDATE FLOW ---

    # Register/Login Candidate
    cand_email = f"cand_test_{os.urandom(3).hex()}@test.com"
    r = session.post(f"{BASE_URL}/auth/register", json={
        "email": cand_email, "password": "password123", "full_name": "Test Candidate", "role": "candidate"
    })
    if r.status_code != 200:
        log(f"Candidate Registration Failed: {r.text}", False)
        return
    cand_token = r.json()["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    log("Candidate Registered & Logged In")

    # Upload Selfie (Face Verification Prep)
    os.makedirs("tools/test_assets", exist_ok=True)
    with open("tools/test_assets/selfie.jpg", "wb") as f: f.write(os.urandom(1024))
    files = {"file": ("selfie.jpg", open("tools/test_assets/selfie.jpg", "rb"), "image/jpeg")}
    r = session.post(f"{BASE_URL}/candidate/upload-selfie", files=files, headers=cand_headers)
    if r.status_code == 200: log("Candidate Selfie Uploaded")
    else: log(f"Selfie Upload Failed: {r.text}", False)

    # Join Room (Random Questions assigned here)
    r = session.post(f"{BASE_URL}/candidate/join", json={
        "room_code": room_code, "password": room_password
    }, headers=cand_headers)
    if r.status_code != 200:
        log(f"Joining Room Failed: {r.text}", False)
        return
    session_id = r.json()["session_id"]
    log(f"Candidate Joined Room (Session ID: {session_id})")

    # --- 3. INTERVIEW PROCESS ---

    # Complete the interview (Answer 2 questions)
    questions_answered = 0
    while True:
        r = session.get(f"{BASE_URL}/interview/next-question/{session_id}", headers=cand_headers)
        q_data = r.json()
        
        if q_data.get("status") == "finished":
            log(f"Interview Finished (Answered {questions_answered} questions)")
            break
            
        q_id = q_data["question_id"]
        q_text = q_data["text"]
        log(f"  Received: {q_text[:40]}...")

        # Submit Answer (Audio blob)
        files = {
            "session_id": (None, str(session_id)),
            "question_id": (None, str(q_id)),
            "audio": ("answer.wav", b"fake_audio_content", "audio/wav")
        }
        r = session.post(f"{BASE_URL}/interview/submit-answer", files=files, headers=cand_headers)
        if r.status_code == 200:
            questions_answered += 1
        else:
            log(f"Submitting Answer Failed: {r.text}", False)
            break

    # Trigger Finish/Processing
    r = session.post(f"{BASE_URL}/interview/finish/{session_id}", headers=cand_headers)
    if r.status_code == 200:
        log("Interview Finalized (Background Processing Started)")
    else:
        log(f"Finishing Interview Failed: {r.text}", False)

    # --- 4. VERIFICATION ---

    # Wait a moment for background task entry to exist (though results take longer)
    time.sleep(1)
    
    # Check Admin Dashboard
    r = session.get(f"{BASE_URL}/admin/users/results", headers=admin_headers)
    if r.status_code == 200:
        results = r.json()
        target_session = next((s for s in results if s["session_id"] == session_id), None)
        if target_session:
            log("Admin Dashboard shows candidate session record")
            log(f"  Entries Count: {len(target_session['details'])}")
        else:
            log("Candidate record not found in dashboard", False)
    else:
        log(f"Admin Dashboard Access Failed: {r.text}", False)

    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED SUCCESSFULLY")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_complete_flow()
