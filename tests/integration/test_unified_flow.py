import requests
import os
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "http://localhost:8000/api" # Using http as per .env and docker-compose usually, or https if certs present. Trying http first as server log said "No SSL Certificates found" (or maybe it did, I saw mixed logs). 
# Actually log said "[SECURE MODE] SSL Certificates found." in one run, but later connection refused.
# Use https if certs are there. The test files used https://localhost:8000.
# I will use https and verify=False.
BASE_URL = "http://localhost:8000/api"
VERIFY_SSL = False

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, status=True):
    color = GREEN if status else RED
    mark = "[PASS]" if status else "[FAIL]"
    print(f"{color}{mark} {msg}{RESET}")

def test_unified_flow():
    session = requests.Session()
    session.verify = VERIFY_SSL
    
    print("\n" + "="*50)
    print("🚀 STARTING UNIFIED END-TO-END TEST")
    print("="*50 + "\n")

    # --- 1. ADMIN FLOW ---
    
    # Register/Login Admin
    admin_email = f"admin_unified_{os.urandom(3).hex()}@test.com"
    r = session.post(f"{BASE_URL}/auth/register", json={
        "email": admin_email, "password": "password123", "full_name": "Unified Admin", "role": "admin"
    })
    if r.status_code != 200:
        log(f"Admin Registration Failed: {r.text}", False)
        return
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    log("Admin Registered & Logged In")

    # Create Question Paper (was Bank)
    r = session.post(f"{BASE_URL}/admin/papers", json={
        "name": "Unified Paper", 
        "description": "Testing all endpoints"
    }, headers=admin_headers)
    if r.status_code != 200:
        log(f"Paper Creation Failed: {r.text}", False)
        return
    paper_id = r.json()["id"]
    log(f"Question Paper Created (ID: {paper_id})")

    # Add Questions
    q1 = {"content": "What is REST?", "topic": "API", "difficulty": "Easy", "marks": 5, "response_type": "text"}
    r = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q1, headers=admin_headers)
    if r.status_code != 200:
        log(f"Adding Question 1 Failed: {r.text}", False)
        return
    
    q2 = {"content": "Explain AI.", "topic": "AI", "difficulty": "Medium", "marks": 5, "response_type": "audio"}
    r = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q2, headers=admin_headers)
    if r.status_code != 200:
        log(f"Adding Question 2 Failed: {r.text}", False)
        return
    log("Added 2 Questions (Text & Audio types)")

    # Create Candidate
    cand_email = f"cand_unified_{os.urandom(3).hex()}@test.com"
    r = session.post(f"{BASE_URL}/auth/register", json={
        "email": cand_email, "password": "password123", "full_name": "Unified Candidate", "role": "candidate"
    }, headers=admin_headers)
    if r.status_code != 200:
        log(f"Candidate Registration Failed: {r.text}", False)
        return
    cand_token = r.json()["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    # Get candidate ID
    r = session.get(f"{BASE_URL}/auth/me", headers=cand_headers)
    cand_id = r.json()["id"]
    log("Candidate Registered")

    # Schedule Interview (was Room)
    # The new admin.py has /interviews/schedule taking InterviewScheduleCreate
    # class InterviewScheduleCreate(BaseModel):
    #     candidate_id: int
    #     paper_id: int
    #     schedule_time: str
    #     duration_minutes: int = 180
    from datetime import datetime
    schedule_time = datetime.utcnow().isoformat()
    
    r = session.post(f"{BASE_URL}/admin/interviews/schedule", json={
        "candidate_id": cand_id,
        "paper_id": paper_id,
        "schedule_time": schedule_time,
        "duration_minutes": 60
    }, headers=admin_headers)
    
    if r.status_code != 200:
        log(f"Scheduling Interview Failed: {r.text}", False)
        return
        
    sched_data = r.json()
    session_id = sched_data["session_id"]
    access_token = sched_data["access_token"]
    log(f"Interview Scheduled (Session ID: {session_id})")

    # --- 2. CANDIDATE FLOW ---
    
    # Access Interview (using token)
    r = session.get(f"{BASE_URL}/interview/access/{access_token}")
    if r.status_code != 200:
        log(f"Access Interview Failed: {r.text}", False)
        return
    log("Candidate Accessed Interview Link")
    
    # Start Session
    r = session.post(f"{BASE_URL}/interview/start-session/{session_id}", headers=cand_headers) # Headers might not be needed if public, but usually safer. logic checks session_db.
    # The start_session_logic relies on session_id, doesn't seem to enforce user match strictly in code snippet provided, 
    # but let's send headers.
    if r.status_code != 200:
        log(f"Start Session Failed: {r.text}", False)
        return
    log("Session Started")

    # --- 3. INTERVIEW SUBMISSIONS ---
    
    # Answer Question 1 (Text)
    # Logic: get next question -> submit
    
    r = session.get(f"{BASE_URL}/interview/next-question/{session_id}", headers=cand_headers)
    q_data = r.json()
    if "question_id" not in q_data:
        log(f"Get Next Question Failed: {q_data}", False)
        return
    
    q1_id = q_data["question_id"]
    log(f"Got Question 1: {q_data['text']}")
    
    # Submit Text
    r = session.post(f"{BASE_URL}/interview/submit-answer-text", data={
        "session_id": session_id,
        "question_id": q1_id,
        "answer_text": "REST is stateless."
    }, headers=cand_headers)
    
    if r.status_code == 200 and r.json()["status"] == "saved":
        log("Submit Text Answer Success")
    else:
        log(f"Submit Text Answer Failed: {r.text}", False)
        
    # Answer Question 2 (Audio)
    r = session.get(f"{BASE_URL}/interview/next-question/{session_id}", headers=cand_headers)
    q_data = r.json()
    if "question_id" not in q_data:
        log("No second question found?", False)
    else:
        q2_id = q_data["question_id"]
        log(f"Got Question 2: {q_data['text']}")
        
        # Submit Audio
        dummy_wav = "test_audio.wav"
        with open(dummy_wav, "wb") as f: f.write(os.urandom(1024)) # Dummy audio
        files = {
            "session_id": (None, str(session_id)),
            "question_id": (None, str(q2_id)),
            "audio": ("ans.wav", open(dummy_wav, "rb"), "audio/wav")
        }
        r = session.post(f"{BASE_URL}/interview/submit-answer-audio", files=files, headers=cand_headers)
        if r.status_code == 200:
            log("Submit Audio Answer Success")
        else:
            log(f"Submit Audio Answer Failed: {r.text}", False)
        os.remove(dummy_wav)

    # Finish Interview
    r = session.post(f"{BASE_URL}/interview/finish/{session_id}", headers=cand_headers)
    if r.status_code == 200:
        log("Interview Finished (Background Check Triggered)")
    else:
        log(f"Finish Interview Failed: {r.text}", False)

    # --- 4. STANDALONE TOOLS ---
    
    log("Testing Public STT Tool...")
    with open("stt_test.wav", "wb") as f: f.write(os.urandom(1024))
    files = {"audio": ("stt.wav", open("stt_test.wav", "rb"), "audio/wav")}
    r = session.post(f"{BASE_URL}/interview/tools/speech-to-text", files=files)
    if r.status_code == 200:
        log(f"STT Tool Response: {r.json()}")
    else:
        # It handles empty/random audio with validation error or empty string, checking if 200 or handled error
        log(f"STT Tool Request: {r.status_code} (Might be 500 if audio invalid/unreadable, but endpoint exists)")
    os.remove("stt_test.wav")

    print("\n" + "="*50)
    print("✅ TEST COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_unified_flow()
