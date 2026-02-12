import requests
import json
import time

BASE_URL = "http://localhost:8001/api"

def audit_endpoint(path, method="GET", body=None):
    url = f"{BASE_URL}{path}"
    print(f"Auditing [{method}] {url}...")
    try:
        # Reduced timeout to 5 seconds as per user request
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=body or {}, timeout=5)
        
        try:
            data = response.json()
        except Exception:
            print(f"  [CRITICAL] Response is not JSON: {response.text[:100]}")
            return False

        required_keys = {"status_code", "data", "message", "success"}
        actual_keys = set(data.keys())
        missing = required_keys - actual_keys
        
        if missing:
            print(f"  [FAIL] Missing standard response keys: {missing}")
            print(f"  Response: {data}")
            return False
        
        print(f"  [OK] Format consistent. success={data.get('success')}, status={data.get('status_code')}")
        return True

    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    endpoints = [
        # Auth
        ("/auth/login", "POST", {"email": "audit@test.com", "password": "any"}),
        ("/auth/token", "POST"), # Should fail 422 because of form data missing, but should be wrapped
        ("/auth/me", "GET"),
        
        # Candidate
        ("/candidate/history", "GET"),
        
        # System
        ("/status/?interview_id=0", "GET"),
        ("/not-found", "GET"),
        
        # Interview
        ("/interview/access/invalid_token", "GET"),
    ]
    
    print("=" * 50)
    print("STARTING COMPREHENSIVE API AUDIT (SCHEMA-BASED)")
    print("Checking for structure: {status_code, data, message, success}")
    print("=" * 50)

    results = []
    for path, method, *rest in endpoints:
        body = rest[0] if rest else None
        results.append(audit_endpoint(path, method, body))
    
    print("=" * 50)
    if all(results):
        print("AUDIT PASSED: All tested endpoints are consistent.")
    else:
        print(f"AUDIT FAILED: {results.count(False)} endpoints had issues.")
