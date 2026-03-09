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
    print("Starting Comprehensive API Test...")
    
    # 1. AUTH: Login as Super Admin
    print("\n[1] Testing Auth Login (Super Admin)...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    assert login_res.status_code == 200, f"Super Admin Login failed: {login_res.status_code} - {login_res.text}"
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Super Admin Login Successful")
 
    # 2. AUTH: Me
    print("\n[2] Testing Auth Me...")
    me_res = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
    assert me_res.status_code == 200, f"Auth Me failed: {me_res.status_code} - {me_res.text}"
    print(f" Auth Me: {me_res.json()['data']['email']} ({me_res.json()['data']['role']})")
 
    # 3. TEAMS: Create Team
    print("\n[3] Testing Team Creation...")
    team_name = f"UNIQUE_TEAM_{uuid.uuid4().hex}"
    print(f"DEBUG: Creating team with name: {team_name}")
    team_res = requests.post(f"{BASE_URL}/super-admin/teams", headers=admin_headers, json={
        "name": team_name,
        "description": "Verification team"
    })
    assert team_res.status_code == 201, f"Team Creation failed for '{team_name}': {team_res.status_code} - {team_res.text}"
    team_id = team_res.json()["data"]["id"]
    print(f" Team Created: {team_name} (ID: {team_id})")

    # 4. TEAMS: List Teams
    print("\n[4] Testing Team Listing...")
    list_teams_res = requests.get(f"{BASE_URL}/super-admin/teams", headers=admin_headers)
    assert list_teams_res.status_code == 200, f"Team Listing failed: {list_teams_res.status_code} - {list_teams_res.text}"
    assert any(t["id"] == team_id for t in list_teams_res.json()["data"]), f"Team ID {team_id} not found in listing"
    print(f" Team List Successful (Found Team ID {team_id})")

    # 4.1 TEAMS: Get One Team
    print("\n[4.1] Testing Get One Team...")
    get_team_res = requests.get(f"{BASE_URL}/super-admin/teams/{team_id}", headers=admin_headers)
    assert get_team_res.status_code == 200, f"Get One Team failed: {get_team_res.status_code} - {get_team_res.text}"
    assert get_team_res.json()["data"]["name"] == team_name, f"Team name mismatch: expected {team_name}, got {get_team_res.json()['data']['name']}"
    print(f" Get One Team Successful: {team_name}")

    # 4.2 TEAMS: Update Team
    print("\n[4.2] Testing Team Update...")
    new_team_name = f"Updated {team_name}"
    update_res = requests.patch(f"{BASE_URL}/super-admin/teams/{team_id}", headers=admin_headers, json={
        "name": new_team_name,
        "description": "Updated description"
    })
    assert update_res.status_code == 200, f"Team Update failed: {update_res.status_code} - {update_res.text}"
    assert update_res.json()["data"]["name"] == new_team_name, f"Updated team name mismatch: expected {new_team_name}, got {update_res.json()['data']['name']}"
    team_name = new_team_name
    print(f" Team Update Successful: {new_team_name}")

    # 5. ADMIN: List Papers
    print("\n[5] Testing Paper Listing...")
    papers_res = requests.get(f"{BASE_URL}/admin/papers", headers=admin_headers)
    assert papers_res.status_code == 200, f"Paper Listing failed: {papers_res.status_code} - {papers_res.text}"
    print(" Paper List Successful")

    # 6. ADMIN: Create Paper (Linked to Team)
    print("\n[6] Testing Paper Creation (Linked to Team)...")
    paper_res = requests.post(f"{BASE_URL}/admin/papers", headers=admin_headers, json={
        "name": f"Test Paper {uuid.uuid4().hex[:6]}",
        "description": "Verification paper",
        "team_id": team_id
    })
    assert paper_res.status_code == 201, f"Paper Creation failed: {paper_res.status_code} - {paper_res.text}"
    paper_id = paper_res.json()["data"]["id"]
    assert paper_res.json()["data"]["team_id"] == team_id, f"Paper team_id mismatch: expected {team_id}, got {paper_res.json()['data']['team_id']}"
    print(f" Paper Created: ID {paper_id}, Team ID {paper_res.json()['data']['team_id']}")

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
        assert gen_res.json()["data"]["team_id"] == team_id, f"AI Paper team_id mismatch: expected {team_id}, got {gen_res.json()['data']['team_id']}"
        print(f" AI Paper Generated: ID {gen_paper_id}, Team ID {gen_res.json()['data']['team_id']}")
    else:
        print(f" AI Paper Generation skipped/failed (Check LLM config/Ollama): {gen_res.status_code} - {gen_res.text}")

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
    assert q_res.status_code == 201, f"Adding Question failed: {q_res.status_code} - {q_res.text}"
    print(" Question Added Successfully")

    # 8. ADMIN: Candidate Lookup / Creation
    print("\n[8] Testing Candidate Lookup...")
    users_res = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    target_candidate = None
    if users_res.status_code == 200:
        target_candidate = next(
            (u for u in users_res.json()["data"] if u.get("email", "").lower() == CANDIDATE_EMAIL.lower()),
            None
        )

    if not target_candidate:
        print(f" Candidate {CANDIDATE_EMAIL} not found in users list, attempting registration...")
        reg_res = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
            "email": CANDIDATE_EMAIL,
            "password": CANDIDATE_PASS,
            "full_name": "Test Candidate",
            "role": "CANDIDATE"
        })
        print(f" Registration response: {reg_res.status_code} - {reg_res.text[:200]}")
        if reg_res.status_code == 201:
            # register returns a Token object with id, email, full_name, role
            token_data = reg_res.json()["data"]
            candidate_id = token_data.get("id")
        elif reg_res.status_code == 400 and "already registered" in reg_res.text.lower():
            # user exists but wasn't in list (pagination?), fetch again
            all_users = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers).json().get("data", [])
            cand = next((u for u in all_users if u.get("email", "").lower() == CANDIDATE_EMAIL.lower()), None)
            assert cand is not None, f"User exists but can't be found: {CANDIDATE_EMAIL}"
            candidate_id = cand.get("id") or cand.get("user_id")
        else:
            assert False, f"Could not register candidate: {reg_res.status_code} - {reg_res.text}"
    else:
        candidate_id = target_candidate.get("id") or target_candidate.get("user_id")

    assert candidate_id is not None, "Failed to get candidate ID"
    print(f" Candidate found/created: ID {candidate_id}")


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
    assert sched_res.status_code == 201, f"Schedule failed: {sched_res.status_code} - {sched_res.text}"
    interview_data = sched_res.json()["data"]["interview"]
    interview_id = interview_data["id"]
    access_token = sched_res.json()["data"]["access_token"]
    assert interview_data["team_id"] == team_id, f"Interview team_id mismatch: expected {team_id}, got {interview_data['team_id']}"
    assert interview_data["interview_round"] == "ROUND_1", f"Interview round mismatch: expected ROUND_1, got {interview_data['interview_round']}"
    print(f" Interview Scheduled: ID {interview_id}, Round: {interview_data['interview_round']}, Team: {interview_data['team_id']}")

    # 10. ADMIN: List Interviews (Verify Team/Round)
    print("\n[10] Testing Interview Listing...")
    interviews_res = requests.get(f"{BASE_URL}/admin/interviews", headers=admin_headers)
    assert interviews_res.status_code == 200, f"Interview Listing failed: {interviews_res.status_code} - {interviews_res.text}"
    my_interview = next((i for i in interviews_res.json()["data"] if i["id"] == interview_id), None)
    assert my_interview is not None, f"Interview ID {interview_id} not found in listing"
    assert my_interview["team_id"] == team_id, f"Listed interview team_id mismatch: expected {team_id}, got {my_interview['team_id']}"
    assert my_interview["interview_round"] == "ROUND_1", f"Listed interview round mismatch: expected ROUND_1, got {my_interview['interview_round']}"
    print(" Interview List Verified (Team/Round present)")

    # 11. ADMIN: Get Interview Detail
    print("\n[11] Testing Interview Detail...")
    detail_res = requests.get(f"{BASE_URL}/admin/interviews/{interview_id}", headers=admin_headers)
    assert detail_res.status_code == 200, f"Interview Detail failed: {detail_res.status_code} - {detail_res.text}"
    assert detail_res.json()["data"]["team_id"] == team_id, f"Detail interview team_id mismatch: expected {team_id}, got {detail_res.json()['data']['team_id']}"
    print(" Interview Detail Verified (Team/Round present)")

    # 12. CANDIDATE: Login & History
    print("\n[12] Testing Candidate Login & History...")
    c_login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": CANDIDATE_EMAIL,
        "password": CANDIDATE_PASS,
        "access_token": access_token
    })
    assert c_login_res.status_code == 200, f"Candidate Login failed: {c_login_res.status_code} - {c_login_res.text}"
    c_token = c_login_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}
    
    c_history = requests.get(f"{BASE_URL}/candidate/history", headers=c_headers)
    assert c_history.status_code == 200, f"Candidate History failed: {c_history.status_code} - {c_history.text}"
    print(" Candidate Login & History Verified")

    # 13. SYSTEM: Status
    print("\n[13] Testing System Status...")
    status_res = requests.get(f"{BASE_URL}/status/", params={"interview_id": interview_id})
    assert status_res.status_code == 200, f"System Status failed: {status_res.status_code} - {status_res.text}"
    print(f" System Status: {status_res.json()['data']['status']}")

    # 14. TEAMS: Delete Team (Cleanup)
    print("\n[14] Testing Team Deletion...")
    # First, try deleting team with paper (should fail)
    del_fail_res = requests.delete(f"{BASE_URL}/super-admin/teams/{team_id}", headers=admin_headers)
    assert del_fail_res.status_code == 400
    print(" Team Deletion Guard Verified (Cannot delete team with attached papers)")

    # Delete paper first (Actually paper deletion might be restricted if used in interviews)
    # So we'll created a temporary team for deletion testing
    print("\n[14.1] Testing Deletion with temporary team...")
    temp_team_res = requests.post(f"{BASE_URL}/super-admin/teams", headers=admin_headers, json={
        "name": f"Temp Team {uuid.uuid4().hex[:6]}",
        "description": "To be deleted"
    })
    temp_team_id = temp_team_res.json()["data"]["id"]
    requests.delete(f"{BASE_URL}/super-admin/teams/{temp_team_id}", headers=admin_headers)
    
    check_temp = requests.get(f"{BASE_URL}/super-admin/teams/{temp_team_id}", headers=admin_headers)
    assert check_temp.status_code == 404
    print(" Temporary Team Deletion Successful")


    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
