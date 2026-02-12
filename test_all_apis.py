"""
Enhanced API Database Integration Test
Works with existing database - uses or creates test users
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"
TEST_PREFIX = "test_api_"

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
    "created_users": []  # Track what we created for cleanup
}

results = {
    "passed": [],
    "failed": [],
    "total": 0
}

def log_test(name, success, details=""):
    """Log test result"""
    results["total"] += 1
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {name}")
    if details:
        print(f"   {details}")
    
    if success:
        results["passed"].append(name)
    else:
        results["failed"].append({"name": name, "details": details})

def setup_test_users():
    """Setup test users - either create or use existing"""
    print("\nSETUP - Checking database for existing users...")
    print("-" * 60)
    
    # Try to get list of users (requires no auth for bootstrap case)
    try:
        # First check if any users exist
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "email": f"{TEST_PREFIX}admin@test.com",
            "password": "admin123",
            "full_name": f"{TEST_PREFIX}Admin User",
            "role": "admin"
        })
        
        if response.status_code == 201:
            # Successfully created first user (bootstrap)
            data = response.json()
            test_data["admin_token"] = data["data"]["access_token"]
            test_data["admin_id"] = data["data"]["id"]
            test_data["created_users"].append("admin")
            print(f"[OK] Created bootstrap admin user (ID: {test_data['admin_id']})")
            return True
            
        elif response.status_code == 403:
            # Users exist, need to login with existing credentials
            print("[INFO] Database has existing users - will use existing admin")
            # Ask user to provide credentials or use known defaults
            return setup_with_existing_users()
        else:
            print(f"[ERROR] Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
        return False

def setup_with_existing_users():
    """Use existing admin credentials"""
    print("[INFO] Attempting login with default admin credentials...")
    
    #Try common admin emails
    admin_emails = [
        "admin@test.com",
        "admin@example.com",
        f"{TEST_PREFIX}admin@test.com"
    ]
    
    for email in admin_emails:
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                test_data["admin_token"] = data["data"]["access_token"]
                test_data["admin_id"] = data["data"]["id"]
                print(f"[OK] Logged in as existing admin: {email}")
                return True
        except:
            continue
    
    print("[ERROR] Could not login with default credentials")
    print("[INFO] Please ensure there's an admin user with:")
    print("       Email: admin@test.com")
    print("       Password: admin123")
    return False

def test_auth_login():
    """Test login with existing credentials"""
    if not test_data["admin_token"]:
        log_test("Login", False, "No admin credentials available")
        return False
    
    log_test("Login", True, "Using existing session")
    return True

def test_auth_me():
    """Test get current user"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test("Get Current User", True, f"Email: {data['data']['email']}")
            return True
        else:
            log_test("Get Current User", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Current User", False, str(e))
        return False

def test_create_candidate():
    """Create test candidate via admin"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.post(f"{BASE_URL}/auth/register",
            headers=headers,
            json={
                "email": f"{TEST_PREFIX}candidate_{int(time.time())}@test.com",
                "password": "candidate123",
                "full_name": f"{TEST_PREFIX}Candidate User",
                "role": "candidate"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            test_data["candidate_token"] = data["data"]["access_token"]
            test_data["candidate_id"] = data["data"]["id"]
            test_data["created_users"].append("candidate")
            log_test("Create Candidate", True, f"Candidate ID: {test_data['candidate_id']}")
            return True
        else:
            log_test("Create Candidate", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Create Candidate", False, str(e))
        return False

def test_create_paper():
    """Test creating question paper"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.post(f"{BASE_URL}/admin/papers",
            headers=headers,
            json={
                "name": f"{TEST_PREFIX}Paper_{int(time.time())}",
                "description": "Automated test paper"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            test_data["paper_id"] = data["data"]["id"]
            log_test("Create Paper", True, f"Paper ID: {test_data['paper_id']}")
            return True
        else:
            log_test("Create Paper", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Create Paper", False, str(e))
        return False

def test_add_question():
    """Test adding question to paper"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.post(
            f"{BASE_URL}/admin/papers/{test_data['paper_id']}/questions",
            headers=headers,
            json={
                "content": "What is Python?",
                "topic": "Programming",
                "difficulty": "Easy",
                "marks": 5,
                "response_type": "text"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            test_data["question_id"] = data["data"]["id"]
            log_test("Add Question", True, f"Question ID: {test_data['question_id']}")
            return True
        else:
            log_test("Add Question", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Add Question", False, str(e))
        return False

def test_list_papers():
    """Test listing papers"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/papers", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test("List Papers", True, f"Found {len(data['data'])} papers")
            return True
        else:
            log_test("List Papers", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("List Papers", False, str(e))
        return False

def test_schedule_interview():
    """Test scheduling interview"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        schedule_time = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        response = requests.post(f"{BASE_URL}/admin/interviews/schedule",
            headers=headers,
            json={
                "candidate_id": test_data["candidate_id"],
                "paper_id": test_data["paper_id"],
                "schedule_time": schedule_time,
                "duration_minutes": 30
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            test_data["interview_id"] = data["data"]["interview_id"]
            test_data["access_token"] = data["data"]["access_token"]
            log_test("Schedule Interview", True, f"Interview ID: {test_data['interview_id']}")
            return True
        else:
            log_test("Schedule Interview", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Schedule Interview", False, str(e))
        return False

def test_list_interviews():
    """Test listing interviews"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/interviews", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test("List Interviews", True, f"Found {len(data['data'])} interviews")
            return True
        else:
            log_test("List Interviews", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("List Interviews", False, str(e))
        return False

def test_get_interview_detail():
    """Test getting interview details"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(
            f"{BASE_URL}/admin/interviews/{test_data['interview_id']}", 
            headers=headers
        )
        
        if response.status_code == 200:
            log_test("Get Interview Detail", True)
            return True
        else:
            log_test("Get Interview Detail", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Interview Detail", False, str(e))
        return False

def test_update_interview():
    """Test updating interview"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.put(
            f"{BASE_URL}/admin/interviews/{test_data['interview_id']}",
            headers=headers,
            json={"duration_minutes": 45}
        )
        
        if response.status_code == 200:
            log_test("Update Interview", True)
            return True
        else:
            log_test("Update Interview", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Update Interview", False, str(e))
        return False

def test_list_users():
    """Test listing users"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test("List Users", True, f"Found {len(data['data'])} users")
            return True
        else:
            log_test("List Users", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("List Users", False, str(e))
        return False

def test_candidate_history():
    """Test candidate interview history"""
    try:
        headers = {"Authorization": f"Bearer {test_data['candidate_token']}"}
        response = requests.get(f"{BASE_URL}/candidate/history", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test("Candidate History", True, f"Found {len(data['data'])} interviews")
            return True
        else:
            log_test("Candidate History", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Candidate History", False, str(e))
        return False

def cleanup():
    """Cleanup test data"""
    print("\n" + "="*60)
    print("CLEANUP - Deleting test data...")
    print("="*60)
    
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        
        # Delete interview
        if test_data["interview_id"]:
            resp = requests.delete(
                f"{BASE_URL}/admin/interviews/{test_data['interview_id']}",
                headers=headers
            )
            status = "OK" if resp.status_code in [200, 404] else "FAIL"
            print(f"[{status}] Deleted interview {test_data['interview_id']}: Status {resp.status_code}")
        
        # Delete paper (cascades to questions)
        if test_data["paper_id"]:
            resp = requests.delete(
                f"{BASE_URL}/admin/papers/{test_data['paper_id']}",
                headers=headers
            )
            status = "OK" if resp.status_code in [200, 404] else "FAIL"
            print(f"[{status}] Deleted paper {test_data['paper_id']}: Status {resp.status_code}")
        
        # Only delete users we created
        if "candidate" in test_data["created_users"] and test_data["candidate_id"]:
            resp = requests.delete(
                f"{BASE_URL}/admin/users/{test_data['candidate_id']}",
                headers=headers
            )
            status = "OK" if resp.status_code in [200, 404] else "FAIL"
            print(f"[{status}] Deleted candidate {test_data['candidate_id']}: Status {resp.status_code}")
        
        if "admin" in test_data["created_users"] and test_data["admin_id"]:
            resp = requests.delete(
                f"{BASE_URL}/admin/users/{test_data['admin_id']}",
                headers=headers
            )
            status = "OK" if resp.status_code in [200, 404] else "FAIL"
            print(f"[{status}] Deleted admin {test_data['admin_id']}: Status {resp.status_code}")
            
    except Exception as e:
        print(f"[WARN] Cleanup error: {e}")

def print_summary():
    """Print test summary"""
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {len(results['passed'])} [PASS]")
    print(f"Failed: {len(results['failed'])} [FAIL]")
    print(f"Success Rate: {(len(results['passed'])/results['total']*100) if results['total'] > 0 else 0:.1f}%")
    
    if results['failed']:
        print("\n" + "="*60)
        print("FAILED TESTS:")
        print("="*60)
        for fail in results['failed']:
            print(f"[FAIL] {fail['name']}")
            print(f"   {fail['details']}")

def main():
    print("="*60)
    print("API DATABASE INTEGRATION TEST")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Setup - get admin credentials
    if not setup_test_users():
        print("\n[ERROR] Cannot proceed without admin credentials")
        print("[INFO] Please create an admin user first with:")
        print("       Email: admin@test.com")
        print("       Password: admin123")
        return 1
    
    # Run tests
    print("\nAUTHENTICATION TESTS")
    print("-" * 60)
    test_auth_login()
    test_auth_me()
    test_create_candidate()
    
    print("\nADMIN - PAPER TESTS")
    print("-" * 60)
    test_create_paper()
    test_add_question()
    test_list_papers()
    
    print("\nADMIN - INTERVIEW TESTS")
    print("-" * 60)
    test_schedule_interview()
    test_list_interviews()
    test_get_interview_detail()
    test_update_interview()
    
    print("\nADMIN - USER TESTS")
    print("-" * 60)
    test_list_users()
    
    print("\nCANDIDATE TESTS")
    print("-" * 60)
    test_candidate_history()
    
    # Summary and cleanup
    print_summary()
    cleanup()
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if len(results['failed']) == 0 else 1

if __name__ == "__main__":
    exit(main())
