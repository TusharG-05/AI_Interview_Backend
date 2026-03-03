import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8001/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"
CANDIDATE_EMAIL = "cand_audit_f913767c@test.com"
CANDIDATE_PASS = "admin123" # Standard test password

def test_api():
    print("🚀 Starting Comprehensive API Test...")
    
    # 1. AUTH: Login as Super Admin
    print("\n[1] Testing Auth Login (Super Admin)...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Super Admin Login Successful")

    # 2. AUTH: Me
    print("\n[2] Testing Auth Me...")
    me_res = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
    assert me_res.status_code == 200
    print(f"✅ Auth Me: {me_res.json()['data']['email']} ({me_res.json()['data']['role']})")

    # 3. TEAMS: Create Team
    print("\n[3] Testing Team Creation...")
    team_name = f"Test Team {uuid.uuid4().hex[:6]}"
    team_res = requests.post(f"{BASE_URL}/super-admin/teams", headers=admin_headers, json={
        "name": team_name,
        "description": "Verification team"
    })
    assert team_res.status_code == 201
    team_id = team_res.json()["data"]["id"]
    print(f"✅ Team Created: {team_name} (ID: {team_id})")

    # 4. TEAMS: List Teams
    print("\n[4] Testing Team Listing...")
    list_teams_res = requests.get(f"{BASE_URL}/super-admin/teams", headers=admin_headers)
    assert list_teams_res.status_code == 200
    assert any(t["id"] == team_id for t in list_teams_res.json()["data"])
    print(f"✅ Team List Successful (Found Team ID {team_id})")

    # 5. ADMIN: List Papers
    print("\n[5] Testing Paper Listing...")
    papers_res = requests.get(f"{BASE_URL}/admin/papers", headers=admin_headers)
    assert papers_res.status_code == 200
    print("✅ Paper List Successful")

    # 6. ADMIN: Create Paper (Linked to Team)
    print("\n[6] Testing Paper Creation (Linked to Team)...")
    paper_res = requests.post(f"{BASE_URL}/admin/papers", headers=admin_headers, json={
        "name": f"Test Paper {uuid.uuid4().hex[:6]}",
        "description": "Verification paper",
        "team_id": team_id
    })
    assert paper_res.status_code == 201
    paper_id = paper_res.json()["data"]["id"]
    print(f"✅ Paper Created: ID {paper_id}, Team ID {paper_res.json()['data']['team_id']}")

    # 6.5 ADMIN: Generate Paper (AI)
    print("\n[6.5] Testing AI Paper Generation (Linked to Team)...")
    gen_res = requests.post(f"{BASE_URL}/admin/generate-paper", headers=admin_headers, json={
        "ai_prompt": "Python and FastAPI basics",
        "years_of_experience": 2,
        "num_questions": 3,
        "team_id": team_id,
        "paper_name": f"AI Paper {uuid.uuid4().hex[:6]}"
    })
    # This might fail if LLM is not configured, so we'll just log and continue if it's not a 201
    if gen_res.status_code == 201:
        gen_paper_id = gen_res.json()["data"]["id"]
        print(f"✅ AI Paper Generated: ID {gen_paper_id}, Team ID {gen_res.json()['data']['team_id']}")
    else:
        print(f"⚠️ AI Paper Generation skipped/failed (Check LLM config/Ollama): {gen_res.status_code} - {gen_res.text}")

    # 7. ADMIN: Add Question
    print("\n[7] Testing Adding Question...")
    q_res = requests.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", headers=admin_headers, json={
        "content": "What is Python?",
        "question_text": "What is Python?",
        "topic": "Python",
        "difficulty": "Easy",
        "marks": 10,
        "response_type": "text"
    })
    assert q_res.status_code == 201
    print("✅ Question Added Successfully")

    # 8. ADMIN: List Candidates (Robust lookup)
    print("\n[8] Testing Candidate Lookup...")
    # Try /admin/users first as it's a simple list and likely contains the candidate
    users_res = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    target_candidate = None
    if users_res.status_code == 200:
        target_candidate = next((u for u in users_res.json()["data"] if u.get("email", "").lower() == CANDIDATE_EMAIL.lower()), None)
    
    if not target_candidate:
         # Try registration
         print(f"⚠️ Candidate {CANDIDATE_EMAIL} not found in users list, attempting registration...")
         reg_res = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
             "email": CANDIDATE_EMAIL,
             "password": CANDIDATE_PASS,
             "full_name": "Test Candidate",
             "role": "CANDIDATE"
         })
         if reg_res.status_code == 201:
             target_candidate = reg_res.json()["data"]
         elif "already registered" in reg_res.text:
             # If already registered, they MUST be in the full list
             all_users = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers).json()["data"]
             target_candidate = next((u for u in all_users if u.get("email", "").lower() == CANDIDATE_EMAIL.lower()), None)

    assert target_candidate is not None, f"Could not find or create candidate {CANDIDATE_EMAIL}"
    candidate_id = target_candidate.get("id") or target_candidate.get("user_id")
    assert candidate_id is not None, "Failed to get candidate ID"
    print(f"✅ Candidate found/created: ID {candidate_id}")

    # 9. ADMIN: Schedule Interview (New Team & Round)
    print("\n[9] Testing Interview Scheduling (Team + Round)...")
    sched_res = requests.post(f"{BASE_URL}/admin/interviews/schedule", headers=admin_headers, json={
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "team_id": team_id,
        "interview_round": "ROUND_1",
        "schedule_time": "2026-03-10T15:00:00Z",
        "duration_minutes": 45
    })
    assert sched_res.status_code == 201, f"Schedule failed: {sched_res.text}"
    interview_data = sched_res.json()["data"]["interview"]
    interview_id = interview_data["id"]
    access_token = sched_res.json()["data"]["access_token"]
    assert interview_data["team_id"] == team_id
    assert interview_data["interview_round"] == "ROUND_1"
    print(f"✅ Interview Scheduled: ID {interview_id}, Round: {interview_data['interview_round']}, Team: {interview_data['team_id']}")

    # 10. ADMIN: List Interviews (Verify Team/Round)
    print("\n[10] Testing Interview Listing...")
    interviews_res = requests.get(f"{BASE_URL}/admin/interviews", headers=admin_headers)
    assert interviews_res.status_code == 200
    my_interview = next((i for i in interviews_res.json()["data"] if i["id"] == interview_id), None)
    assert my_interview is not None
    assert my_interview["team_id"] == team_id
    assert my_interview["interview_round"] == "ROUND_1"
    print("✅ Interview List Verified (Team/Round present)")

    # 11. ADMIN: Get Interview Detail
    print("\n[11] Testing Interview Detail...")
    detail_res = requests.get(f"{BASE_URL}/admin/interviews/{interview_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["team_id"] == team_id
    print("✅ Interview Detail Verified (Team/Round present)")

    # 12. CANDIDATE: Login & History
    print("\n[12] Testing Candidate Login & History...")
    c_login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": CANDIDATE_EMAIL,
        "password": CANDIDATE_PASS,
        "access_token": access_token
    })
    if c_login_res.status_code != 200:
        print(f"❌ Candidate Login Failed: {c_login_res.status_code} - {c_login_res.text}")
        print(f"Debug: Email: {CANDIDATE_EMAIL}, Pass: {CANDIDATE_PASS}, Token: {access_token}")
    assert c_login_res.status_code == 200
    c_token = c_login_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}
    
    c_history = requests.get(f"{BASE_URL}/candidate/history", headers=c_headers)
    assert c_history.status_code == 200
    print("✅ Candidate Login & History Verified")

    # 13. SYSTEM: Status
    print("\n[13] Testing System Status...")
    status_res = requests.get(f"{BASE_URL}/status/", params={"interview_id": interview_id})
    assert status_res.status_code == 200
    print(f"✅ System Status: {status_res.json()['data']['status']}")

    print("\n✨ ALL TESTS PASSED SUCCESSFULLY! ✨")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
