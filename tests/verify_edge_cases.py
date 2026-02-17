import requests
import json
import sys
import uuid

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "password123"
INVALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid"

LOG_FILE = "edge_case_results.txt"

def log(msg, status="INFO"):
    entry = f"[{status}] {msg}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def check(response, expected_status=200, context=""):
    expected_list = expected_status if isinstance(expected_status, list) else [expected_status]
    if response.status_code in expected_list:
        log(f"PASS: {context} -> Got {response.status_code}", "PASS")
        return True
    else:
        log(f"FAIL: {context} -> Expected {expected_list}, Got {response.status_code}", "FAIL")
        try:
            log(f"Response: {response.json()}", "DEBUG")
        except:
            log(f"Response: {response.text}", "DEBUG")
        return False

def main():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Starting Edge Case Verification...\n")

    session = requests.Session()

    # --- 1. Authentication Edge Cases ---
    log("--- Auth Edge Cases ---")
    
    # 1.1 Invalid Login
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": "wrong@test.com", "password": "wrong"})
    check(resp, 401, "Invalid Login")

    # 1.2 Access Protected Route without Token
    no_auth_session = requests.Session()
    resp = no_auth_session.get(f"{BASE_URL}/admin/papers")
    check(resp, 401, "Access sans Token")

    # 1.3 Access with Invalid Token
    headers = {"Authorization": INVALID_TOKEN}
    resp = no_auth_session.get(f"{BASE_URL}/admin/papers", headers=headers)
    check(resp, 401, "Access with Invalid Token")

    # Get Valid Token for Further Tests
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if not check(resp, 200, "Valid Admin Login"):
        return
    token = resp.json()['data']['access_token']
    session.headers.update({"Authorization": f"Bearer {token}"})

    # --- 2. Registration Edge Cases ---
    log("--- Registration Edge Cases ---")
    
    # 2.1 Duplicate Email
    # Try to register admin again (should fail if email exists)
    # Note: Using /auth/register requires admin usually, checking if endpoint is open
    reg_payload = {
        "email": ADMIN_EMAIL,
        "password": "password123",
        "full_name": "Clone Admin",
        "role": "admin"
    }
    resp = session.post(f"{BASE_URL}/auth/register", json=reg_payload)
    check(resp, 400, "Register Duplicate Email")
    
    # --- 3. Resource Management Edge Cases ---
    log("--- Resource Edge Cases ---")

    # 3.1 Create Paper - Empty Name (Pydantic Validation)
    # Pydantic usually returns 422
    resp = session.post(f"{BASE_URL}/admin/papers", json={"name": "", "description": "Empty"})
    # Pydantic might allow empty string unless constr(min_length=1) is used. Let's check.
    # If it allows, it's a weak point we found.
    if resp.status_code == 201:
        log("WARN: API allowed creating paper with empty name", "WARN")
    else:
        check(resp, 422, "Create Paper Empty Name")
        
    # 3.2 Add Question to Non-existent Paper
    resp = session.post(f"{BASE_URL}/admin/papers/999999/questions", json={
        "content": "Ghost Question", "difficulty": "Easy", "marks": 5, "response_type": "audio"
    })
    check(resp, 404, "Add Question to Invalid Paper")
    
    # 3.3 Get Non-existent Question
    resp = session.get(f"{BASE_URL}/admin/questions/999999")
    check(resp, 404, "Get Invalid Question")
    
    # 3.4 Delete Non-existent Paper
    resp = session.delete(f"{BASE_URL}/admin/papers/999999")
    check(resp, 404, "Delete Invalid Paper")

    # --- 4. Scheduling Logic Edge Cases ---
    log("--- Scheduling Edge Cases ---")
    
    # Need a valid candidate ID
    c_resp = session.get(f"{BASE_URL}/admin/candidates")
    candidate_id = None
    if c_resp.status_code == 200:
        candidates = c_resp.json().get('data', [])
        if candidates: candidate_id = candidates[0].get('id')
    
    # Need a valid paper ID
    p_resp = session.post(f"{BASE_URL}/admin/papers", json={"name": "Edge Case Paper", "description": "Temp"})
    paper_id = p_resp.json()['data']['id'] if p_resp.status_code == 201 else None

    if candidate_id and paper_id:
        # 4.1 Schedule with Invalid Candidate
        resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json={
            "candidate_id": 999999,
            "paper_id": paper_id,
            "schedule_time": "2026-12-31T10:00:00",
            "duration_minutes": 60
        })
        check(resp, 400, "Schedule Invalid Candidate")

        # 4.2 Schedule with Invalid Paper
        resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json={
            "candidate_id": candidate_id,
            "paper_id": 999999,
            "schedule_time": "2026-12-31T10:00:00",
            "duration_minutes": 60
        })
        check(resp, 400, "Schedule Invalid Paper")

        # 4.3 Schedule in Past (Logic Check)
        resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json={
            "candidate_id": candidate_id,
            "paper_id": paper_id,
            "schedule_time": "2020-01-01T10:00:00",
            "duration_minutes": 60
        })
        # If API doesn't prevent past scheduling, this will return 201 (WARN)
        if resp.status_code == 201:
            log("WARN: API allowed scheduling interview in the past", "WARN")
        else:
            check(resp, 400, "Schedule in Past")
            
        # Cleanup
        session.delete(f"{BASE_URL}/admin/papers/{paper_id}")
    else:
        log("Skipping scheduling tests - could not setup prereqs", "WARN")

    log("Edge Case Verification Complete.")

if __name__ == "__main__":
    main()
