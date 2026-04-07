import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_tab_switch():
    print("🚀 Starting Tab Switch API Verification...")
    
    # 1. Login as Admin
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    }).json()
    admin_token = admin_login['data']['access_token']
    print("✅ Admin logged in")

    # 2. Schedule an Interview
    # We need a candidate_id and paper_id. Let's list and pick first.
    papers = requests.get(f"{BASE_URL}/admin/papers", headers={"Authorization": f"Bearer {admin_token}"}).json()
    paper_id = papers['data'][0]['id']
    
    candidates = requests.get(f"{BASE_URL}/admin/candidates", headers={"Authorization": f"Bearer {admin_token}"}).json()
    candidate_id = candidates['data']['items'][0]['id']
    candidate_email = candidates['data']['items'][0]['email']
    
    schedule_resp = requests.post(f"{BASE_URL}/admin/interviews/schedule", 
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "candidate_id": candidate_id,
            "paper_id": paper_id,
            "schedule_time": "2026-03-02T15:00:00Z",
            "duration_minutes": 60,
            "allow_copy_paste": False
        }).json()
    
    interview_id = schedule_resp['data']['interview']['id']
    access_token = schedule_resp['data']['interview']['access_token']
    print(f"✅ Interview scheduled (ID: {interview_id})")

    # 3. Candidate Login/Access
    cand_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": candidate_email,
        "password": "test123", # Assuming default password from previous tests
        "access_token": access_token
    }).json()
    cand_token = cand_login['data']['access_token']
    print("✅ Candidate logged in")

    # 4. Call Tab Switch API multiple times
    for i in range(1, 4):
        print(f"\n📡 Tab Switch Attempt {i}...")
        resp = requests.post(f"{BASE_URL}/interview/{interview_id}/tab-switch", 
            headers={"Authorization": f"Bearer {cand_token}"}).json()
        
        print(f"Response: {json.dumps(resp, indent=2)}")
        
        if resp['status_code'] == 200:
            count = resp['data']['warning_count']
            max_w = resp['data']['max_warnings']
            print(f"✅ Received Warning {count}/{max_w}")
        elif resp['status_code'] == 403:
             print(f"🛑 403 Forbidden: {resp['message']}")
             if resp['data'].get('is_suspended'):
                 print(f"🚨 Session SUSPENDED: {resp['data'].get('reason')}")
    
    # 5. Final Check - Get session status from Admin side
    print("\n🔍 Final session check from Admin dashboard...")
    status = requests.get(f"{BASE_URL}/admin/interviews/{interview_id}", 
        headers={"Authorization": f"Bearer {admin_token}"}).json()
    
    print(f"Session Status: {status['data']['status']}")
    print(f"Warning Count: {status['data'].get('warning_count')}")
    print(f"Suspended: {status['data'].get('is_suspended')}")

if __name__ == "__main__":
    test_tab_switch()
