import requests
import json
import time
import os

# Use the requested v1 link
BASE_URL = "https://ichigo253-ai-interview-backend.hf.space/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"
CANDIDATE_EMAIL = "tushar@chicmicstudios.in"
CANDIDATE_PASS = "tush#4184"

TIMEOUT = 120 # High timeout for HF

def log_response(response, title):
    print(f"\n[{time.strftime('%H:%M:%S')}] === {title} ===")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    except:
        print(f"Raw Output: {response.text[:500]}...")
        return None

def run_tab_switch_test():
    total_start = time.time()
    
    # 1. Admin Login
    print("Step 1: Admin Login...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=TIMEOUT)
    data = log_response(resp, "Admin Login")
    admin_token = data["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Add/Find Candidate
    print("\nStep 2: Finding candidate...")
    candidate_id = None
    users_resp = requests.get(f"{BASE_URL}/admin/users", headers=headers, timeout=TIMEOUT)
    users_data = users_resp.json().get("data", [])
    for user in users_data:
        if user["email"].lower() == CANDIDATE_EMAIL.lower():
            candidate_id = user["id"]
            print(f"Found existing candidate! ID: {candidate_id}")
            break
    
    if not candidate_id:
        print("Error: Could not find candidate. Aborting.")
        return

    # 3. Create a quick paper
    print("\nStep 3: Creating Paper...")
    paper_resp = requests.post(
        f"{BASE_URL}/admin/papers",
        headers=headers,
        json={"name": "Tab Switch Test Paper", "description": "Assessment for tab switch testing"},
        timeout=TIMEOUT
    )
    data = log_response(paper_resp, "Create Paper")
    paper_id = data["data"]["id"]

    # 4. Add 1 Question
    requests.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", headers=headers, json={"content": "Test item", "topic": "Test", "marks": 5, "response_type": "text"}, timeout=TIMEOUT)

    # 5. Schedule Interview
    print("\nStep 4: Scheduling Interview...")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    schedule_data = {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "schedule_time": now,
        "duration_minutes": 60,
        "interview_round": "ROUND_1"
    }
    sch_resp = requests.post(f"{BASE_URL}/admin/interviews/schedule", headers=headers, json=schedule_data, timeout=TIMEOUT)
    data = log_response(sch_resp, "Schedule Interview")
    access_token = data["data"]["access_token"]
    interview_id = data["data"]["interview"]["id"]

    # 6. Candidate Login
    print("\nStep 5: Candidate Login...")
    cand_login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASS, "access_token": access_token},
        timeout=TIMEOUT
    )
    data = log_response(cand_login_resp, "Candidate Login")
    cand_token = data["data"]["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}

    # 7. Start Session
    print("\nStep 6: Starting Interview Session...")
    requests.post(f"{BASE_URL}/interview/start-session/{interview_id}", headers=cand_headers, timeout=TIMEOUT)

    # 8. Perform Tab Switches
    print("\nStep 7: Performing Tab Switches...")
    for i in range(1, 4):
        print(f"Tab Switch {i}...")
        ts_resp = requests.post(
            f"{BASE_URL}/interview/{interview_id}/tab-switch",
            headers=cand_headers,
            json={"event_type": "TAB_SWITCH"},
            timeout=TIMEOUT
        )
        data = log_response(ts_resp, f"Tab Switch {i}")
        
        if data and data.get("status_code") == 403:
            print(f"Interview suspended as expected on switch {i}!")
            break
        time.sleep(1)

    # 9. Verify Final Status via Admin
    print("\nStep 8: Verifying Final Status as Admin...")
    status_resp = requests.get(f"{BASE_URL}/admin/interviews/{interview_id}", headers=headers, timeout=TIMEOUT)
    data = log_response(status_resp, "Final Interview Status")
    
    if data and data["data"]["is_suspended"] and data["data"]["suspension_reason"] == "multiple_tab_switch":
        print("\n✅ TEST PASSED: Interview successfully suspended for multiple tab switches.")
    else:
        print("\n❌ TEST FAILED: Interview state is not what was expected.")

    print(f"\nTotal Time: {time.time() - total_start:.2f}s")

if __name__ == "__main__":
    run_tab_switch_test()
