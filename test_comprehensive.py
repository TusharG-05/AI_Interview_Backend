"""
Comprehensive API Test - All Remaining Endpoints
Tests 45+ endpoints across all routers
"""
import requests
import json
import time
from datetime import datetime, timedelta
import io

BASE_URL = "http://localhost:8000/api"
TEST_PREFIX = "test_comprehensive_"

# Test data storage
test_data = {
    "admin_token": None,
    "candidate_token": None,
    "admin_id": None,
    "candidate_id": None,
    "paper_id": None,
    "question_id": None,
    "interview_id": None,
    "access_token": None,
    "created_users": []
}

results = {
    "passed": [],
    "failed": [],
    "skipped": [],
    "total": 0
}

def log_test(name, success, details="", skip=False):
    """Log test result"""
    results["total"] += 1
    if skip:
        status = "[SKIP]"
        results["skipped"].append(name)
    else:
        status = "[PASS]" if success else "[FAIL]"
        if success:
            results["passed"].append(name)
        else:
            results["failed"].append({"name": name, "details": details})
    
    print(f"{status} - {name}")
    if details and not skip:
        print(f"   {details}")

def setup_admin():
    """Setup admin credentials"""
    print("\n[SETUP] Getting admin credentials...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            data = response.json()
            test_data["admin_token"] = data["data"]["access_token"]
            test_data["admin_id"] = data["data"]["id"]
            print(f"[OK] Admin logged in (ID: {test_data['admin_id']})")
            return True
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
    return False

# ==================== AUTH TESTS ====================
def test_auth_token():
    """Test OAuth2 token endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data={
            "username": "admin@test.com",
            "password": "admin123"
        })
        success = 200 <= response.status_code < 300
        log_test("POST /auth/token (OAuth2)", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("POST /auth/token", False, str(e))

# ==================== ADMIN - PAPERS TESTS ====================
def test_get_paper_detail():
    """Test get single paper"""
    if not test_data["paper_id"]:
        log_test("GET /admin/papers/{id}", False, "No paper_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/papers/{test_data['paper_id']}", headers=headers)
        success = 200 <= response.status_code < 300
        log_test("GET /admin/papers/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/papers/{id}", False, str(e))

def test_update_paper():
    """Test update paper"""
    if not test_data["paper_id"]:
        log_test("PATCH /admin/papers/{id}", False, "No paper_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.patch(
            f"{BASE_URL}/admin/papers/{test_data['paper_id']}",
            headers=headers,
            json={"description": "Updated description"}
        )
        success = 200 <= response.status_code < 300
        log_test("PATCH /admin/papers/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("PATCH /admin/papers/{id}", False, str(e))

def test_get_paper_questions():
    """Test get questions for a paper"""
    if not test_data["paper_id"]:
        log_test("GET /admin/papers/{id}/questions", False, "No paper_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(
            f"{BASE_URL}/admin/papers/{test_data['paper_id']}/questions",
            headers=headers
        )
        success = 200 <= response.status_code < 300
        if success and response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            log_test("GET /admin/papers/{id}/questions", True, f"Found {count} questions")
        else:
            log_test("GET /admin/papers/{id}/questions", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/papers/{id}/questions", False, str(e))

# ==================== ADMIN - QUESTIONS TESTS ====================
def test_list_all_questions():
    """Test list all questions"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/questions", headers=headers)
        success = 200 <= response.status_code < 300
        if success and response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            log_test("GET /admin/questions", True, f"Found {count} questions")
        else:
            log_test("GET /admin/questions", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/questions", False, str(e))

def test_get_question_detail():
    """Test get single question"""
    if not test_data["question_id"]:
        log_test("GET /admin/questions/{id}", False, "No question_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/questions/{test_data['question_id']}", headers=headers)
        success = 200 <= response.status_code < 300
        log_test("GET /admin/questions/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/questions/{id}", False, str(e))

def test_update_question():
    """Test update question"""
    if not test_data["question_id"]:
        log_test("PATCH /admin/questions/{id}", False, "No question_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.patch(
            f"{BASE_URL}/admin/questions/{test_data['question_id']}",
            headers=headers,
            json={"marks": 10}
        )
        success = 200 <= response.status_code < 300
        log_test("PATCH /admin/questions/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("PATCH /admin/questions/{id}", False, str(e))

# ==================== ADMIN - INTERVIEWS TESTS ====================
def test_update_interview():
    """Test update interview"""
    if not test_data["interview_id"]:
        log_test("PATCH /admin/interviews/{id}", False, "No interview_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.patch(
            f"{BASE_URL}/admin/interviews/{test_data['interview_id']}",
            headers=headers,
            json={"duration_minutes": 60}
        )
        success = 200 <= response.status_code < 300
        log_test("PATCH /admin/interviews/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("PATCH /admin/interviews/{id}", False, str(e))

def test_get_live_status():
    """Test get live interview status"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/interviews/live-status", headers=headers)
        success = 200 <= response.status_code < 300
        if success and response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            log_test("GET /admin/interviews/live-status", True, f"Found {count} live interviews")
        else:
            log_test("GET /admin/interviews/live-status", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/interviews/live-status", False, str(e))

# ==================== ADMIN - USERS TESTS ====================
def test_create_test_user():
    """Test create user via admin"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.post(f"{BASE_URL}/admin/users",
            headers=headers,
            json={
                "email": f"{TEST_PREFIX}user_{int(time.time())}@test.com",
                "password": "test123",
                "full_name": f"{TEST_PREFIX}Test User",
                "role": "candidate"
            }
        )
        success = 200 <= response.status_code < 300
        if success and response.status_code == 201:
            data = response.json()
            test_data["created_users"].append(data["data"]["id"])
            log_test("POST /admin/users", True, f"Created user ID: {data['data']['id']}")
        else:
            log_test("POST /admin/users", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("POST /admin/users", False, str(e))

def test_get_user_detail():
    """Test get single user"""
    if not test_data["admin_id"]:
        log_test("GET /admin/users/{id}", False, "No user_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/users/{test_data['admin_id']}", headers=headers)
        success = 200 <= response.status_code < 300
        log_test("GET /admin/users/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/users/{id}", False, str(e))

def test_update_user():
    """Test update user"""
    if not test_data["created_users"]:
        log_test("PATCH /admin/users/{id}", False, "No test user", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        user_id = test_data["created_users"][0]
        response = requests.patch(
            f"{BASE_URL}/admin/users/{user_id}",
            headers=headers,
            json={"full_name": "Updated Name"}
        )
        success = 200 <= response.status_code < 300
        log_test("PATCH /admin/users/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("PATCH /admin/users/{id}", False, str(e))

def test_get_candidates():
    """Test get all candidates"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/candidates", headers=headers)
        success = 200 <= response.status_code < 300
        if success and response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            log_test("GET /admin/candidates", True, f"Found {count} candidates")
        else:
            log_test("GET /admin/candidates", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/candidates", False, str(e))

# ==================== ADMIN - RESULTS TESTS ====================
def test_get_all_results():
    """Test get all results"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/users/results", headers=headers)
        success = 200 <= response.status_code < 300
        if success and response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            log_test("GET /admin/users/results", True, f"Found {count} results")
        else:
            log_test("GET /admin/users/results", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/users/results", False, str(e))

def test_get_single_result():
    """Test get result for specific interview"""
    if not test_data["interview_id"]:
        log_test("GET /admin/results/{interview_id}", False, "No interview_id", skip=True)
        return
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(
            f"{BASE_URL}/admin/results/{test_data['interview_id']}",
            headers=headers
        )
        success = 200 <= response.status_code < 300
        log_test("GET /admin/results/{interview_id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /admin/results/{interview_id}", False, str(e))

# ==================== SETTINGS TESTS ====================
def test_get_settings():
    """Test get settings"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/settings/", headers=headers)
        success = 200 <= response.status_code < 300
        log_test("GET /settings/", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /settings/", False, str(e))

# ==================== INTERVIEW TESTS ====================
def test_interview_access():
    """Test interview access endpoint"""
    if not test_data["access_token"]:
        log_test("GET /interview/access/{token}", False, "No access token", skip=True)
        return
    
    try:
        response = requests.get(f"{BASE_URL}/interview/access/{test_data['access_token']}")
        success = 200 <= response.status_code < 300
        log_test("GET /interview/access/{token}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /interview/access/{token}", False, str(e))

def test_start_interview_session():
    """Test start interview session"""
    if not test_data["interview_id"]:
        log_test("POST /interview/start-session/{id}", False, "No interview_id", skip=True)
        return
    
    try:
        response = requests.post(
            f"{BASE_URL}/interview/start-session/{test_data['interview_id']}"
        )
        success = 200 <= response.status_code < 300
        log_test("POST /interview/start-session/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("POST /interview/start-session/{id}", False, str(e))

def test_get_next_question():
    """Test get next question"""
    if not test_data["interview_id"]:
        log_test("GET /interview/next-question/{id}", False, "No interview_id", skip=True)
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/interview/next-question/{test_data['interview_id']}"
        )
        success = 200 <= response.status_code < 300
        log_test("GET /interview/next-question/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /interview/next-question/{id}", False, str(e))

# ==================== MAIN EXECUTION ====================
def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {len(results['passed'])} [PASS]")
    print(f"Failed: {len(results['failed'])} [FAIL]")
    print(f"Skipped: {len(results['skipped'])} [SKIP]")
    success_rate = (len(results['passed'])/results['total']*100) if results['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if results['failed']:
        print("\n" + "="*60)
        print("FAILED TESTS:")
        print("="*60)
        for fail in results['failed']:
            print(f"[FAIL] {fail['name']}")
            if fail['details']:
                print(f"   {fail['details']}")

def main():
    print("="*60)
    print("COMPREHENSIVE API ENDPOINT TEST")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Setup
    if not setup_admin():
        print("[ERROR] Cannot proceed without admin credentials")
        return 1
    
    # Create test data first
    print("\n[PHASE 0] SETUP - Creating Test Data")
    print("-" * 60)
    
    # Create test paper if needed
    headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
    resp = requests.post(f"{BASE_URL}/admin/papers", headers=headers,
        json={"name": f"{TEST_PREFIX}paper", "description": "Test"})
    if 200 <= resp.status_code < 300:
        test_data["paper_id"] = resp.json()["data"]["id"]
        print(f"[OK] Created paper ID: {test_data['paper_id']}")
        
        # Add question
        resp = requests.post(
            f"{BASE_URL}/admin/papers/{test_data['paper_id']}/questions",
            headers=headers,
            json={"content": "Test Q?", "topic": "Test", "difficulty": "Easy",
                  "marks": 5, "response_type": "text"}
        )
        if 200 <= resp.status_code < 300:
            test_data["question_id"] = resp.json()["data"]["id"]
            print(f"[OK] Created question ID: {test_data['question_id']}")
    
    # Create candidate
    resp = requests.post(f"{BASE_URL}/auth/register", headers=headers,
        json={"email": f"{TEST_PREFIX}cand@test.com", "password": "test123",
              "full_name": "Test Candidate", "role": "candidate"})
    if 200 <= resp.status_code < 300:
        test_data["candidate_id"] = resp.json()["data"]["id"]
        test_data["created_users"].append(test_data["candidate_id"])
        print(f"[OK] Created candidate ID: {test_data['candidate_id']}")
        
        # Schedule interview
        if test_data["paper_id"] and test_data["candidate_id"]:
            schedule_time = (datetime.now() + timedelta(minutes=5)).isoformat()
            resp = requests.post(f"{BASE_URL}/admin/interviews/schedule",
                headers=headers,
                json={"candidate_id": test_data["candidate_id"],
                      "paper_id": test_data["paper_id"],
                      "schedule_time": schedule_time,
                      "duration_minutes": 30})
            if 200 <= resp.status_code < 300:
                data = resp.json()["data"]
                test_data["interview_id"] = data["interview_id"]
                test_data["access_token"] = data["access_token"]
                print(f"[OK] Created interview ID: {test_data['interview_id']}")
    
    # Run tests
    print("\n[PHASE 1] AUTH ENDPOINTS")
    print("-" * 60)
    test_auth_token()
    
    print("\n[PHASE 2] ADMIN - PAPERS")
    print("-" * 60)
    test_get_paper_detail()
    test_update_paper()
    test_get_paper_questions()
    
    print("\n[PHASE 3] ADMIN - QUESTIONS")
    print("-" * 60)
    test_list_all_questions()
    test_get_question_detail()
    test_update_question()
    
    print("\n[PHASE 4] ADMIN - INTERVIEWS")
    print("-" * 60)
    test_update_interview()
    test_get_live_status()
    
    print("\n[PHASE 5] ADMIN - USERS")
    print("-" * 60)
    test_create_test_user()
    test_get_user_detail()
    test_update_user()
    test_get_candidates()
    
    print("\n[PHASE 6] ADMIN - RESULTS")
    print("-" * 60)
    test_get_all_results()
    test_get_single_result()
    
    print("\n[PHASE 7] SETTINGS")
    print("-" * 60)
    test_get_settings()
    
    print("\n[PHASE 8] INTERVIEW FLOW")
    print("-" * 60)
    test_interview_access()
    test_start_interview_session()
    test_get_next_question()
    
    # Summary
    print_summary()
    
    # Cleanup
    print("\n[CLEANUP] Deleting test data...")
    for user_id in test_data["created_users"]:
        requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=headers)
    if test_data["paper_id"]:
        requests.delete(f"{BASE_URL}/admin/papers/{test_data['paper_id']}", headers=headers)
    if test_data["interview_id"]:
        requests.delete(f"{BASE_URL}/admin/interviews/{test_data['interview_id']}", headers=headers)
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0 if len(results['failed']) == 0 else 1

if __name__ == "__main__":
    exit(main())
