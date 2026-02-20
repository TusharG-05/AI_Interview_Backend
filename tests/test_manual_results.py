
import sys
import os
import requests
import json

# Adjust path to find app if needed, though we will run against live server or using TestClient
# Here we use requests against localhost
BASE_URL = "http://localhost:8000"

def login_admin():
    # Assuming a default admin exists or we can create one
    # Try logging in with default credentials from previous context or generic
    urls = [
        ("admin@example.com", "admin123"),
        ("admin@test.com", "admin123") 
    ]
    
    for email, pwd in urls:
        resp = requests.post(f"{BASE_URL}/api/auth/token", data={"username": email, "password": pwd})
        if resp.status_code == 200:
            print(f"Logged in as {email}")
            return resp.json()["access_token"]
        else:
            print(f"Login failed for {email}: {resp.status_code} {resp.text}")
    
    print("Failed to login as admin. Please ensure server is running and admin exists.")
    sys.exit(1)

def verify_structure(data):
    if not isinstance(data, dict):
        print(f"FAIL: Expected dict, got {type(data)}")
        return False
        
    required_keys = ["id", "interview", "interview_response", "total_score", "created_at"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"FAIL: Missing top level keys: {missing}")
        return False
        
    # Check Interview Nested
    interview = data.get("interview")
    if not isinstance(interview, dict):
        print("FAIL: 'interview' is not a dict")
        return False
        
    session_keys = ["id", "access_token", "admin", "candidate", "paper", "status"]
    missing_session = [k for k in session_keys if k not in interview]
    if missing_session:
        print(f"FAIL: Missing session keys: {missing_session}")
        return False
        
    # Check Admin/Candidate Nested
    if interview.get("admin") and "email" not in interview["admin"]:
        print("FAIL: Admin object missing email")
        return False
        
    if interview.get("paper") and "name" not in interview["paper"]:
        print("FAIL: Paper object missing name")
        return False

    # Check Answers
    answers = data.get("interview_response")
    if not isinstance(answers, list):
        print("FAIL: 'interview_response' is not a list")
        return False
        
    if answers:
        ans = answers[0]
        if "question" not in ans:
            print("FAIL: Answer missing 'question' object")
            return False
        if "question_id" in ans:
            print("FAIL: 'question_id' should not be present in answer object")
            return False
            
    print("SUCCESS: JSON structure matches requirements")
    return True

def main():
    token = login_admin()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- Testing Single Result ---")
    # Fetch list first to get an ID
    resp = requests.get(f"{BASE_URL}/api/admin/interviews", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to list interviews: {resp.text}")
        sys.exit(1)
        
    interviews = resp.json()['data']
    if not interviews:
        print("No interviews found to test.")
        sys.exit(0)
        
    target_id = interviews[0]['id']
    print(f"Testing Result for Interview ID: {target_id}")
    
    # Check single result
    resp = requests.get(f"{BASE_URL}/api/admin/results/{target_id}", headers=headers)
    if resp.status_code == 200:
        data = resp.json()['data']
        print(json.dumps(data, indent=2))
        verify_structure(data)
    elif resp.status_code == 404:
         print("Result not found (expected if interview not started/finished).")
    else:
        print(f"Error fetching result: {resp.status_code} {resp.text}")

    print("\n--- Testing All Results List ---")
    resp = requests.get(f"{BASE_URL}/api/admin/users/results", headers=headers)
    if resp.status_code == 200:
        data_list = resp.json()['data']
        print(f"Found {len(data_list)} results")
        if data_list:
            verify_structure(data_list[0])
    else:
        print(f"Error fetching list: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
