import requests
import json
import os
import time

BASE_URL = "https://ichigo253-ai-interview-backend.hf.space"

def print_result(name, url, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name} ({url})")
    if details:
        print(f"    -> {details}")

def test_status_endpoint():
    url = f"{BASE_URL}/api/status/?interview_id=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        success = response.status_code == 200 and data.get("success") == True and data["data"]["status"] == "online"
        details = data["data"]["services"]["llm"] if success else response.text
        print_result("System Status", url, success, f"LLM Status: {details}")
        return success
    except Exception as e:
        print_result("System Status", url, False, str(e))
        return False

def test_auth_login_fail():
    url = f"{BASE_URL}/api/auth/login"
    try:
        # Expected to fail (401) with invalid credentials, proving the endpoint is active
        response = requests.post(
            url, 
            data={"username": "test@example.com", "password": "wrongpassword"},
            timeout=10
        )
        success = response.status_code in [401, 422, 404]
        print_result("Auth Login (Negative Test)", url, success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_result("Auth Login", url, False, str(e))
        return False

def test_docs_accessibility():
    url = f"{BASE_URL}/docs"
    try:
        response = requests.get(url, timeout=10)
        success = response.status_code == 200
        print_result("Swagger API Docs", url, success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_result("Swagger API Docs", url, False, str(e))
        return False

def run_all_tests():
    print(f"\n🚀 Running Comprehensive API Tests against: {BASE_URL}\n")
    
    results = [
        test_status_endpoint(),
        test_auth_login_fail(),
        test_docs_accessibility()
    ]
    
    print("\n" + "="*40)
    if all(results):
        print("🟢 ALL CORE ENDPOINTS RESPONDING CORRECTLY")
        return True
    else:
        print("🔴 SOME ENDPOINTS FAILED")
        return False

if __name__ == "__main__":
    run_all_tests()
