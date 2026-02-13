"""
Phase 2: File Upload & Streaming Tests
Tests remaining endpoints including uploads and real-time features
"""
import requests
import json
import time
from datetime import datetime
import io
from PIL import Image

BASE_URL = "http://localhost:8000/api"

test_data = {
    "admin_token": None,
    "candidate_token": None,
    "candidate_id": None
}

results = {"passed": [], "failed": [], "skipped": [], "total": 0}

def log_test(name, success, details="", skip=False):
    results["total"] += 1
    status = "[SKIP]" if skip else ("[PASS]" if success else "[FAIL]")
    if skip:
        results["skipped"].append(name)
    elif success:
        results["passed"].append(name)
    else:
        results["failed"].append({"name": name, "details": details})
    
    print(f"{status} - {name}")
    if details and not skip:
        print(f"   {details}")

def setup():
    """Setup credentials"""
    print("\n[SETUP] Getting credentials...")
    
    # Admin login
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })
    if resp.status_code == 200:
        test_data["admin_token"] = resp.json()["data"]["access_token"]
        print("[OK] Admin logged in")
    
    # Create or login as candidate
    headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
    resp = requests.post(f"{BASE_URL}/auth/register", headers=headers, json={
        "email": f"test_upload_{int(time.time())}@test.com",
        "password": "test123",
        "full_name": "Test Upload User",
        "role": "candidate"
    })
    if 200 <= resp.status_code < 300:
        data = resp.json()["data"]
        test_data["candidate_token"] = data["access_token"]
        test_data["candidate_id"] = data["id"]
        print(f"[OK] Candidate created (ID: {test_data['candidate_id']})")
        return True
    return False

# ==================== CANDIDATE TESTS ====================
def test_upload_selfie():
    """Test candidate selfie upload"""
    try:
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        headers = {"Authorization": f"Bearer {test_data['candidate_token']}"}
        files = {"selfie": ("test.jpg", img_bytes, "image/jpeg")}
        
        response = requests.post(
            f"{BASE_URL}/candidate/upload-selfie",
            headers=headers,
            files=files
        )
        success = 200 <= response.status_code < 300
        log_test("POST /candidate/upload-selfie", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("POST /candidate/upload-selfie", False, str(e))

def test_get_profile_image():
    """Test get profile image"""
    if not test_data["candidate_id"]:
        log_test("GET /candidate/profile-image/{id}", False, "No candidate_id", skip=True)
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/candidate/profile-image/{test_data['candidate_id']}"
        )
        success = 200 <= response.status_code < 300 or response.status_code == 404
        log_test("GET /candidate/profile-image/{id}", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /candidate/profile-image/{id}", False, str(e))

# ==================== STATUS TESTS ====================  
def test_get_status():
    """Test system status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/status/?interview_id=1")
        success = 200 <= response.status_code < 300
        log_test("GET /status/ (System Health)", success, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /status/", False, str(e))

# ==================== ADMIN DELETE TESTS ====================
def test_delete_paper():
    """Test delete paper endpoint"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        
        # Create paper to delete
        resp = requests.post(f"{BASE_URL}/admin/papers", headers=headers,
            json={"name": "Delete Test Paper", "description": "For deletion"})
        if 200 <= resp.status_code < 300:
            paper_id = resp.json()["data"]["id"]
            
            # Delete it
            response = requests.delete(f"{BASE_URL}/admin/papers/{paper_id}", headers=headers)
            success = 200 <= response.status_code < 300
            log_test("DELETE /admin/papers/{id}", success, f"Status: {response.status_code}")
        else:
            log_test("DELETE /admin/papers/{id}", False, "Could not create test paper", skip=True)
    except Exception as e:
        log_test("DELETE /admin/papers/{id}", False, str(e))

def test_delete_question():
    """Test delete question endpoint"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        
        # Create paper and question
        resp = requests.post(f"{BASE_URL}/admin/papers", headers=headers,
            json={"name": "Q Delete Test", "description": "For deletion"})
        if 200 <= resp.status_code < 300:
            paper_id = resp.json()["data"]["id"]
            
            resp = requests.post(f"{BASE_URL}/admin/papers/{paper_id}/questions",
                headers=headers,
                json={"content": "Delete me?", "topic": "Test", "difficulty": "Easy",
                      "marks": 1, "response_type": "text"})
            if 200 <= resp.status_code < 300:
                question_id = resp.json()["data"]["id"]
                
                # Delete question
                response = requests.delete(f"{BASE_URL}/admin/questions/{question_id}", headers=headers)
                success = 200 <= response.status_code < 300
                log_test("DELETE /admin/questions/{id}", success, f"Status: {response.status_code}")
                
                # Cleanup paper
                requests.delete(f"{BASE_URL}/admin/papers/{paper_id}", headers=headers)
            else:
                log_test("DELETE /admin/questions/{id}", False, "Could not create question", skip=True)
        else:
            log_test("DELETE /admin/questions/{id}", False, "Could not create paper", skip=True)
    except Exception as e:
        log_test("DELETE /admin/questions/{id}", False, str(e))

def test_delete_interview():
    """Test delete interview endpoint"""
    log_test("DELETE /admin/interviews/{id}", False, "Tested in previous script", skip=True)

def test_delete_user():
    """Test delete user endpoint"""
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        
        # Create user to delete
        resp = requests.post(f"{BASE_URL}/admin/users", headers=headers,
            json={"email": f"delete_{int(time.time())}@test.com",
                  "password": "test123", "full_name": "Delete Me", "role": "candidate"})
        if 200 <= resp.status_code < 300:
            user_id = resp.json()["data"]["id"]
            
            # Delete user
            response = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=headers)
            success = 200 <= response.status_code < 300
            log_test("DELETE /admin/users/{id}", success, f"Status:{response.status_code}")
        else:
            log_test("DELETE /admin/users/{id}", False, "Could not create test user", skip=True)
    except Exception as e:
        log_test("DELETE /admin/users/{id}", False, str(e))

# ==================== VIDEO/STREAMING TESTS ====================
def test_video_endpoints():
    """Test video endpoints (likely need WebRTC setup)"""
    log_test("GET /video/video_feed", False, "Requires camera stream setup", skip=True)
    log_test("POST /video/offer", False, "Requires WebRTC client", skip=True)
    log_test("POST /video/watch/{id}", False, "Requires active session", skip=True)

# ==================== MAIN ====================
def print_summary():
    print("\n" + "="*60)
    print("PHASE 2 TEST SUMMARY")
    print("="*60)
    print(f"Total: {results['total']}")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")
    
    if results['failed']:
        print("\nFAILURES:")
        for fail in results['failed']:
            print(f"  [FAIL] {fail['name']}: {fail['details']}")

def main():
    print("="*60)
    print("PHASE 2: FILE UPLOADS & ADDITIONAL ENDPOINTS")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not setup():
        print("[ERROR] Setup failed")
        return 1
    
    print("\n[PHASE 1] CANDIDATE ENDPOINTS")
    print("-" * 60)
    test_upload_selfie()
    test_get_profile_image()
    
    print("\n[PHASE 2] SYSTEM STATUS")
    print("-" * 60)
    test_get_status()
    
    print("\n[PHASE 3] DELETE OPERATIONS")
    print("-" * 60)
    test_delete_paper()
    test_delete_question()
    test_delete_interview()
    test_delete_user()
    
    print("\n[PHASE 4] VIDEO/STREAMING")
    print("-" * 60)
    test_video_endpoints()
    
    print_summary()
    
    # Cleanup
    if test_data["candidate_id"]:
        headers = {"Authorization": f"Bearer {test_data['admin_token']}"}
        requests.delete(f"{BASE_URL}/admin/users/{test_data['candidate_id']}", headers=headers)
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0 if len(results['failed']) == 0 else 1

if __name__ == "__main__":
    exit(main())
