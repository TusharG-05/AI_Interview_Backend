import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "password123"
CANDIDATE_EMAIL = "candidate@test.com"

LOG_FILE = "verification_results.txt"

def log(msg, status="INFO"):
    entry = f"[{status}] {msg}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def check(response, expected_status=200):
    expected_list = expected_status if isinstance(expected_status, list) else [expected_status]
    if response.status_code in expected_list:
        log(f"SUCCESS: {response.url} [{response.status_code}]", "PASS")
        return True
    else:
        log(f"FAILURE: {response.url} [{response.status_code}] not in {expected_list}", "FAIL")
        try:
            log(f"Response: {response.json()}", "DEBUG")
        except:
            log(f"Response: {response.text}", "DEBUG")
            
        # If strict 201 was expected but we got 200, maybe we should warn but allow?
        # For now, failure is failure. 
        # But we will update call sites to pass [200, 201]
        return False

def main():
    # Clear log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Starting Verification Scan...\n")

    session = requests.Session()
    
    # 1. Login
    log("Testing Admin Login...")
    login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    resp = session.post(f"{BASE_URL}/auth/login", json=login_payload)
    if not check(resp, 200):
        log("Cannot proceed without login.", "CRITICAL")
        return

    token = resp.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    session.headers.update(headers)
    log("Admin logged in successfully.")

    # 2. Create Paper
    log("Testing Create Paper...")
    paper_payload = {"name": "Test Paper Auto", "description": "Created by verification script"}
    resp = session.post(f"{BASE_URL}/admin/papers", json=paper_payload)
    if not check(resp, 201): return
    paper_id = resp.json()['data']['id']
    log(f"Created Paper ID: {paper_id}")

    # 3. Add Question
    log("Testing Add Question...")
    q_payload = {
        "content": "What is AI?",
        "topic": "General",
        "difficulty": "Easy",
        "marks": 5,
        "response_type": "audio"
    }
    resp = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q_payload)
    check(resp, 201)

    # 4. Get Candidate ID (Need to find the user likely created by setup script)
    # We don't have a direct "get user by email" endpoint for admins easily exposed in the list I saw?
    # Actually /admin/users/results might show users, or I can just use a known ID if setup_admin ran.
    # But setup_admin doesn't return the ID.
    # I'll search for the candidate in the database or loop through candidates if possible.
    # The /admin/candidates endpoint exists!
    log("Fetching Candidate List...")
    resp = session.get(f"{BASE_URL}/admin/candidates")
    candidate_id = None
    if check(resp, 200):
        candidates = resp.json().get('data', [])
        for c in candidates:
             # structure might be dict or object, let's check
             if c.get('email') == CANDIDATE_EMAIL:
                 candidate_id = c.get('id')
                 break
        if not candidate_id and candidates:
             candidate_id = candidates[0].get('id')
    
    if not candidate_id:
        log("No candidate found to schedule interview with.", "WARN")
    else:
        log(f"Found Candidate ID: {candidate_id}")
        
        # 5. Schedule Interview
        log("Testing Schedule Interview...")
        schedule_payload = {
            "candidate_id": candidate_id,
            "paper_id": paper_id,
            "schedule_time": "2026-12-31T10:00:00",
            "duration_minutes": 60
        }
        resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json=schedule_payload)
        check(resp, 201)
        interview_id = resp.json()['data']['interview_id']
        log(f"Scheduled Interview ID: {interview_id}")

    # 6. List Interviews
    log("Testing List Interviews...")
    resp = session.get(f"{BASE_URL}/admin/interviews")
    check(resp, 200)

    # 7. Live Status
    log("Testing Live Status Dashboard...")
    resp = session.get(f"{BASE_URL}/admin/interviews/live-status")
    check(resp, 200)
    
    # 8. Test Deletion Safety (Should Fail 400 because interview exists)
    log(f"Testing Deletion Safety for Paper ID: {paper_id}...")
    resp = session.delete(f"{BASE_URL}/admin/papers/{paper_id}")
    if resp.status_code == 400:
        log("SUCCESS: Deletion blocked as expected (Paper in use)", "PASS")
    else:
        log(f"FAILURE: Deletion not blocked correctly. Status: {resp.status_code}", "FAIL")
    
    # 9. Cleanup
    log(f"Cleaning up Interview ID: {interview_id}...")
    resp = session.delete(f"{BASE_URL}/admin/interviews/{interview_id}")
    check(resp, 200)

    log(f"Cleaning up Paper ID: {paper_id}...")
    resp = session.delete(f"{BASE_URL}/admin/papers/{paper_id}")
    check(resp, 200)

    log("Verification Complete.")

if __name__ == "__main__":
    main()
