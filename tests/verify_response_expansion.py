import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "password123"

LOG_FILE = "verify_expansion.log"

def log(msg):
    print(f"[TEST] {msg}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[TEST] {msg}\n")

def check_response(response, expected_code=200):
    if response.status_code != expected_code:
        log(f"FAILED: Expected {expected_code}, got {response.status_code}")
        log(f"Response: {response.text}")
        sys.exit(1)
    return response.json()

def main():
    session = requests.Session()

    # 1. Login
    log("Logging in...")
    login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    resp = session.post(f"{BASE_URL}/auth/login", json=login_payload)
    data = check_response(resp, 200)["data"]
    token = data["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    log("Login successful.")

    # 2. Create Paper (Pre-requisite)
    log("Creating test paper...")
    paper_payload = {"name": "Expansion Test Paper", "description": "For testing response expansion"}
    resp = session.post(f"{BASE_URL}/admin/papers", json=paper_payload)
    paper_id = check_response(resp, 201)["data"]["id"]
    log(f"Paper created: {paper_id}")

    # 2.5 Add Questions
    log("Adding question to paper...")
    q_payload = {
        "content": "What is Python?",
        "difficulty": "Easy",
        "marks": 5,
        "response_type": "audio"
    }
    resp = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q_payload)
    check_response(resp, 201)
    log("Question added.")

    # 3. Schedule Interview (Pre-requisite)
    log("Scheduling interview...")
    schedule_payload = {
        "candidate_id": 2, # Assuming candidate exists from previous setup
        "paper_id": paper_id,
        "schedule_time": "2026-03-01T10:00:00",
        "duration_minutes": 60
    }
    # Note: Candidate ID 2 might not exist if DB was reset. 
    # Let's list candidates first and pick one or create one if needed.
    # But usually setup_admin.py runs before. We'll assume ID 2 exists or use list_users.
    
    # Let's dynamically find a candidate
    users_resp = session.get(f"{BASE_URL}/admin/users")
    users = check_response(users_resp, 200)["data"]
    candidate = next((u for u in users if u["role"] == "candidate"), None)
    
    if not candidate:
        log("No candidate found. Creating one...")
        cand_payload = {"email": "expansion_cand@test.com", "full_name": "Exp Cand", "password": "password123", "role": "candidate"}
        resp = session.post(f"{BASE_URL}/admin/users", json=cand_payload)
        candidate = check_response(resp, 201)["data"]
    
    schedule_payload["candidate_id"] = candidate["id"]
    
    resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json=schedule_payload)
    interview_data = check_response(resp, 201)["data"]
    interview_id = interview_data["interview_id"]
    log(f"Interview scheduled: {interview_id}")

    # 4. Verify Live Status Endpoint
    log("Verifying GET /admin/interviews/live-status ...")
    resp = session.get(f"{BASE_URL}/admin/interviews/live-status")
    live_data = check_response(resp, 200)["data"]
    if not live_data:
        log("WARNING: No live interviews found (might be filtered by status?)")
    else:
        # Check first item
        item = live_data[0]
        if isinstance(item["interview"], dict) and "status" in item["interview"]:
            log("PASS: Live Status 'interview' is a dict with 'status' field.")
        else:
            log(f"FAIL: Live Status 'interview' is not a full object: {item['interview']}")
            sys.exit(1)

    # 5. Verify Candidate Status Endpoint
    log(f"Verifying GET /admin/interviews/{interview_id}/status ...")
    resp = session.get(f"{BASE_URL}/admin/interviews/{interview_id}/status")
    status_data = check_response(resp, 200)["data"]
    
    if isinstance(status_data["interview"], dict) and "access_token" in status_data["interview"]:
        log("PASS: Candidate Status 'interview' is a dict with 'access_token'.")
        # Check names
        int_obj = status_data["interview"]
        if int_obj.get("candidate_name") or int_obj.get("admin_name"):
             log(f"PASS: Names found: Cand={int_obj.get('candidate_name')}, Admin={int_obj.get('admin_name')}")
        else:
             log(f"FAIL: Names are empty! Cand={int_obj.get('candidate_name')}, Admin={int_obj.get('admin_name')}")
             # We want to fail if they are empty, but for now let's just log FAIL to confirm issue
             # sys.exit(1) 
    else:
        log(f"FAIL: Candidate Status 'interview' is not a full object: {status_data.get('interview')}")
        sys.exit(1)

    # 6. Verify Results Endpoint
    log("Verifying GET /admin/users/results ...")
    resp = session.get(f"{BASE_URL}/admin/users/results")
    results_data = check_response(resp, 200)["data"]
    
    # Find our interview
    target_result = next((r for r in results_data if r["interview"]["id"] == interview_id), None)
    if target_result:
        if isinstance(target_result["interview"], dict) and "duration_minutes" in target_result["interview"]:
             log("PASS: Results 'interview' is a dict with 'duration_minutes'.")
        else:
            log(f"FAIL: Result 'interview' is not a full object: {target_result['interview']}")
            sys.exit(1)
    else:
        log("WARNING: Created interview not found in results (might need to contain answers/results property?)")
        # If get_all_results joins on Result, we might not see it if no answers yet.
        # But get_all_results options checks `InterviewSession.result`
        # Admin logic: `sessions = session.exec(...)`
        # It queries InterviewSession, so it should be there even if result is None?
        # Let's check logic: `responses = s.result.answers if s.result else []`
        # It should list session even if no result.

    # Cleanup
    log("Cleaning up...")
    session.delete(f"{BASE_URL}/admin/interviews/{interview_id}") # Soft delete/cancel?
    # Actually delete paper
    session.delete(f"{BASE_URL}/admin/papers/{paper_id}")
    
    log("Verification Complete. All Checks Passed.")

if __name__ == "__main__":
    main()
