import requests
import sys
import uuid
import datetime
import time

BASE_URL = "http://127.0.0.1:8000/api"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, success=True):
    color = GREEN if success else RED
    print(f"{color}[{'SUCCESS' if success else 'FAIL'}] {msg}{RESET}")

def verify_persistence():
    try:
        # 1. Admin Login
        admin_email = "admin@test.com"
        admin_pass = "admin123"
        print("1. Admin Login...")
        login_resp = requests.post(f"{BASE_URL}/auth/token", data={"username": admin_email, "password": admin_pass})
        if login_resp.status_code != 200:
             print(f"Login Failed: {login_resp.text}")
             return
        
        token_data = login_resp.json()
        print(f"DEBUG: Token Data Type: {type(token_data)}")
        if isinstance(token_data, str):
             print(f"DEBUG: Token Data Content: {token_data}")
             import json
             token_data = json.loads(token_data)

        token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Setup (Cand + Bank + Q + Schedule)
        unique_id = uuid.uuid4().hex[:8]
        cand_email = f"verify_{unique_id}@example.com"
        
        # Create Candidate
        print(f"Creating Candidate {cand_email}...")
        c_resp = requests.post(f"{BASE_URL}/admin/users", json={"email": cand_email, "full_name": f"Tester {unique_id}", "password": "pass", "role": "candidate"}, headers=headers)
        print(f"DEBUG: Create Cand Status: {c_resp.status_code}")
        
        if c_resp.status_code not in [200, 201]:
             print(f"Failed to create candidate: {c_resp.text}")
             return
             
        cand_id = c_resp.json()["id"]
        # Skip list users
        
        # Create Bank
        bank_resp = requests.post(f"{BASE_URL}/admin/banks", json={"name": f"Bank {unique_id}", "description": "Test"}, headers=headers)
        bank_id = bank_resp.json()["id"]
        
        # Add Question
        requests.post(f"{BASE_URL}/admin/banks/{bank_id}/questions", json={"content": "What is 2+2?", "topic": "Math", "difficulty": "Easy", "marks": 10}, headers=headers)
        
        # Schedule
        sched_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
        sched_resp = requests.post(
            f"{BASE_URL}/admin/interviews/schedule",
            json={"candidate_id": cand_id, "bank_id": bank_id, "schedule_time": sched_time, "duration_minutes": 60},
            headers=headers
        )
        session_id = sched_resp.json()["session_id"]
        print(f"   Session {session_id} Scheduled.")
        
        # 3. Get Questions (Trigger session assignment)
        # Even without Access Token, let's see if we can get questions via the public(ish) API? 
        # Actually /interview/session/{id}/questions is public in current impl (checked router).
        qs_resp = requests.get(f"{BASE_URL}/interview/session/{session_id}/questions")
        q_id = qs_resp.json()[0]["id"]
        
        # 4. Submit Answer
        print("4. Submitting Text Answer...")
        ans_resp = requests.post(
            f"{BASE_URL}/interview/submit-text-answer",
            json={"session_id": session_id, "question_id": q_id, "answer_text": "The answer is 4."}
        )
        if ans_resp.status_code != 200:
            log(f"Submission Failed: {ans_resp.text}", False)
            return

        # 5. Finish Interview (Triggers Processing)
        print("5. Finishing Interview & Waiting for AI...")
        fin_resp = requests.post(f"{BASE_URL}/interview/finish/{session_id}")
        if fin_resp.status_code != 200:
             log(f"Finish Failed: {fin_resp.text}", False)
             return
             
        # Wait for Background Task
        for i in range(10):
            sys.stdout.write(f".")
            sys.stdout.flush()
            time.sleep(1)
        print()
        
        # 6. Verify Score
        print("6. Verifying Score Persistence...")
        # Get Admin Interviews
        sessions_resp = requests.get(f"{BASE_URL}/admin/interviews", headers=headers)
        sessions = sessions_resp.json()
        
        target_session = next((s for s in sessions if s['id'] == session_id), None)
        
        if not target_session:
            log("Session not found in admin list!", False)
        elif target_session.get("score") is not None and target_session.get("score") > 0:
            log(f"Persistence Verified! Score: {target_session['score']}", True)
        else:
            log(f"Verification Failed. Score is missing or zero: {target_session}", False)

    except Exception as e:
        import traceback
        traceback.print_exc()
        log(f"Script Error: {e}", False)

if __name__ == "__main__":
    verify_persistence()
