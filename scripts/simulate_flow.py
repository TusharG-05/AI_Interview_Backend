import requests
import sys
import uuid
import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, success=True):
    color = GREEN if success else RED
    print(f"{color}[{'SUCCESS' if success else 'FAIL'}] {msg}{RESET}")

def run_simulation():
    try:
        # 1. Create Admin
        admin_email = "admin@test.com"
        admin_pass = "admin123"
        print("1. Creating/Getting Admin...")
        
        # Try login first
        login_resp = requests.post(f"{BASE_URL}/auth/token", data={"username": admin_email, "password": admin_pass})
        if login_resp.status_code != 200:
             print(f"Admin Login Failed: {login_resp.status_code} {login_resp.text}")
             return
        
        # Token Management
        token = login_resp.json().get("access_token")
        if not token:
            print(f"Failed to get admin token: {login_resp.text}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        log("Admin Logged In")

        # 2. Create Candidate
        candidate_email = f"cand_{uuid.uuid4().hex[:8]}@example.com"
        print(f"2. Creating Candidate {candidate_email}...")
        cand_resp = requests.post(
            f"{BASE_URL}/admin/users", 
            json={"email": candidate_email, "full_name": "Sim Candidate", "password": "pass", "role": "candidate"},
            headers=headers
        )
        if cand_resp.status_code not in [200, 201]:
             print(f"Failed: {cand_resp.text}")
             return
        
        candidate_id = cand_resp.json()["id"]
        log(f"Candidate Created (ID: {candidate_id})")

        # 3. Create Question Bank
        print("3. Creating Question Bank...")
        bank_resp = requests.post(f"{BASE_URL}/admin/banks", json={"name": "Sim Bank", "description": "Simulation"}, headers=headers)
        if bank_resp.status_code not in [200, 201]:
             print(f"Failed Bank Creation: {bank_resp.text}")
             return
        bank_id = bank_resp.json()["id"]
        log(f"Bank Created (ID: {bank_id})")
        
        # 4. Add Question
        print("4. Adding Question...")
        q_resp = requests.post(
            f"{BASE_URL}/admin/banks/{bank_id}/questions",
            json={"content": "What is 2+2?", "topic": "Math", "difficulty": "Easy", "marks": 5},
            headers=headers
        )
        if q_resp.status_code not in [200, 201]:
            print(f"Failed Question Creation: {q_resp.text}")
            return
        log("Question Added")

        # 5. Schedule Interview
        print("5. Scheduling Interview...")
        # Schedule for NOW (or 1 min later) so we can Access immediately?
        # If we schedule for +5 min, access says WAIT.
        # But we want to test Question Fetching. Access usually allows fetching if token is valid?
        # My interview.py logic: if now < schedule_time: return WAIT.
        # So I won't get JoinRoomResponse with "START".
        # Does Get Questions API enforce time?
        # I didn't add time check to Get Questions API. So it should work!
        # Let's schedule for +5 mins.
        
        sched_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
        sched_resp = requests.post(
            f"{BASE_URL}/admin/interviews/schedule",
            json={
                "candidate_id": candidate_id,
                "bank_id": bank_id,
                "schedule_time": sched_time,
                "duration_minutes": 60
            },
            headers=headers
        )
        if sched_resp.status_code != 200:
            print(f"Failed Schedule: {sched_resp.text}")
            return
            
        session_data = sched_resp.json()
        session_id = session_data["session_id"]
        access_token = session_data["access_token"]
        log(f"Interview Scheduled (Session: {session_id})")

        # --- CANDIDATE FLOW ---
        
        # 6. Join/Access
        print("6. Candidate Joining...")
        join_resp = requests.get(f"{BASE_URL}/interview/access/{access_token}")
        if join_resp.status_code != 200:
             # Even 403 would be a failure.
             if "WAIT" in join_resp.text or "Wait" in join_resp.text: 
                  # Access endpoint returns 200 with message="WAIT" for early access?
                  # Let's check logic: return JoinRoomResponse(..., message="WAIT", ...)
                  # So status is 200 OK.
                  log("Join Validated (Status: WAIT - as expected)")
             else:
                  print(f"Failed Join: {join_resp.text}")
        else:
             msg = join_resp.json().get("message", "")
             log(f"Join Successful (Status: {msg})")

        # 7. Get Questions (The New API)
        print("7. Fetching Questions...")
        
        qs_resp = requests.get(f"{BASE_URL}/interview/session/{session_id}/questions")
        if qs_resp.status_code == 200:
            qs = qs_resp.json()
            log(f"Fetched {len(qs)} Questions")
            if len(qs) > 0:
                q_id = qs[0]["id"]
                
                # 8. Submit Answer
                print("8. Submitting Text Answer...")
                ans_resp = requests.post(
                    f"{BASE_URL}/interview/submit-text-answer",
                    json={"session_id": session_id, "question_id": q_id, "answer_text": "Four"}
                )
                if ans_resp.status_code == 200:
                    log("Answer Submitted")
                else:
                    log(f"Answer Failed: {ans_resp.text}", False)
            else:
                log("No questions returned!", False)
        else:
                log(f"Fetch Failed: {qs_resp.status_code} {qs_resp.text}", False)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Simulation Error: {e}")

if __name__ == "__main__":
    run_simulation()
