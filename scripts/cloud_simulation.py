import requests
import time
import uuid
import sys
import json
import argparse
from datetime import datetime, timedelta

# Configuration defaults
DEFAULT_BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"
CANDIDATE_EMAIL = f"candidate_sim_{uuid.uuid4().hex[:6]}@example.com"
CANDIDATE_PASSWORD = "password123"

# Tracking for the comparison table
api_results = []

def record_api(endpoint, method, status_code, success, env):
    api_results.append({
        "endpoint": endpoint,
        "method": method,
        "status": status_code,
        "success": success,
        "env": env
    })

def print_step(msg):
    print(f"\n{'='*50}\n[STEP] {msg}\n{'='*50}")

def print_result(msg, data=None):
    print(f" -> {msg}")
    if data:
        print(f"    Data: {json.dumps(data, indent=2)}")

def run_simulation(base_url, env_name):
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    # Disable SSL verification for local self-signed certs
    session.verify = False
    
    # Suppress InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print(f"Starting simulation against: {base_url} ({env_name})")

    # ---------------------------------------------------------
    # 1. Admin Login & Setup
    # ---------------------------------------------------------
    print_step("1. Admin Login & Setup")
    
    # Try login first
    print(f"Attempting Admin Login for {ADMIN_EMAIL}...")
    try:
        resp = session.post(f"{base_url}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        record_api("/auth/login", "POST", resp.status_code, resp.ok, env_name)
    except Exception as e:
        record_api("/auth/login", "POST", "ERROR", False, env_name)
        print(f"Connection Error: {e}")
        return False

    if resp.status_code == 401:
        print("Admin not found, registering...")
        resp = session.post(f"{base_url}/auth/register", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "full_name": "Sim Admin", "role": "admin"
        })
        record_api("/auth/register", "POST", resp.status_code, resp.ok, env_name)
        
        if resp.ok:
            print("Registration success, logging in...")
            resp = session.post(f"{base_url}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print_result("Admin Logged In")
    else:
        print(f"Admin Login Failed: {resp.text}")
        return False

    # Create Question Paper
    print("Creating Question Paper...")
    paper_data = {"name": f"Sim Paper {uuid.uuid4().hex[:4]}", "description": "E2E Test Paper"}
    resp = session.post(f"{base_url}/admin/papers", json=paper_data)
    record_api("/admin/papers", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    paper_id = resp.json()["data"]["id"]
    print_result(f"Paper Created: ID {paper_id}")

    # Add Questions
    print("Adding Questions...")
    q1 = {"content": "What is Python?", "topic": "Tech", "difficulty": "Easy", "marks": 10, "response_type": "text"}
    resp = session.post(f"{base_url}/admin/papers/{paper_id}/questions", json=q1)
    record_api("/admin/papers/{id}/questions", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    q1_id = resp.json()["data"]["id"]

    q2 = {"content": "Explain AI.", "topic": "AI", "difficulty": "Medium", "marks": 20, "response_type": "text"}
    resp = session.post(f"{base_url}/admin/papers/{paper_id}/questions", json=q2)
    record_api("/admin/papers/{id}/questions", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    q2_id = resp.json()["data"]["id"]
    
    print_result(f"Added 2 Questions: {q1_id}, {q2_id}")

    # ---------------------------------------------------------
    # 2. Candidate Setup & Scheduling
    # ---------------------------------------------------------
    print_step("2. Candidate Setup & Scheduling")
    
    # Register Candidate
    print(f"Registering Candidate: {CANDIDATE_EMAIL}...")
    resp = session.post(f"{base_url}/auth/register", json={
        "email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD, "full_name": "Sim Candidate", "role": "candidate"
    })
    record_api("/auth/register", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    candidate_id = resp.json()["data"]["id"]
    print_result(f"Candidate Registered: ID {candidate_id}")

    # Schedule Interview
    print("Scheduling Interview...")
    schedule_data = {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "schedule_time": (datetime.utcnow() + timedelta(minutes=1)).isoformat(),
        "duration_minutes": 60,
        "max_questions": 2
    }
    resp = session.post(f"{base_url}/admin/interviews/schedule", json=schedule_data)
    record_api("/admin/interviews/schedule", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    interview_data = resp.json()["data"]
    interview_id = interview_data.get("interview_id") or interview_data.get("interview", {}).get("id")
    access_token = interview_data.get("access_token")
    print_result(f"Interview Scheduled: ID {interview_id}")

    # Access Link
    print("Accessing Interview Link...")
    candidate_session = requests.Session()
    candidate_session.verify = False
    resp = candidate_session.get(f"{base_url}/interview/access/{access_token}")
    record_api("/interview/access/{token}", "GET", resp.status_code, resp.ok, env_name)
    
    # If early, update time via Admin
    if resp.status_code == 200 and resp.json().get("data", {}).get("message") == "WAIT":
        print("  -> Updating schedule time to NOW for immediate access...")
        update_data = {"schedule_time": datetime.utcnow().isoformat()}
        session.patch(f"{base_url}/admin/interviews/{interview_id}", json=update_data)
        resp = candidate_session.get(f"{base_url}/interview/access/{access_token}")

    if not resp.ok: return False
    print_result("Access Granted")

    # Start Session
    print("Starting Session...")
    files = {"enrollment_audio": ("enroll.wav", b"riff", "audio/wav")}
    resp = candidate_session.post(f"{base_url}/interview/start-session/{interview_id}", files=files)
    record_api("/interview/start-session/{id}", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    print_result("Session Started")

    # Fetch Q1
    resp = candidate_session.get(f"{base_url}/interview/next-question/{interview_id}")
    record_api("/interview/next-question/{id}", "GET", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    q1_id_fetched = resp.json()["data"]["question_id"]

    # Submit Q1
    ans_data = {"interview_id": interview_id, "question_id": q1_id_fetched, "answer_text": "Python."}
    resp = candidate_session.post(f"{base_url}/interview/submit-answer-text", data=ans_data)
    record_api("/interview/submit-answer-text", "POST", resp.status_code, resp.ok, env_name)
    
    # Finish
    resp = candidate_session.post(f"{base_url}/interview/finish/{interview_id}")
    record_api("/interview/finish/{id}", "POST", resp.status_code, resp.ok, env_name)
    if not resp.ok: return False
    print_result("Finished")

    # Deletion Test (The recent fix!)
    print_step("6. Deletion Verification")
    print("Deleting Question...")
    resp = session.delete(f"{base_url}/admin/questions/{q1_id}")
    record_api("/admin/questions/{id}", "DELETE", resp.status_code, resp.ok, env_name)
    if resp.ok:
        print_result("Question Deleted Successfully (Cascade worked!)")
    else:
        print(f"Question Deletion Failed: {resp.text}")

    print("Deleting Interview...")
    resp = session.delete(f"{base_url}/admin/interviews/{interview_id}")
    record_api("/admin/interviews/{id}", "DELETE", resp.status_code, resp.ok, env_name)
    if resp.ok:
        print_result("Interview Deleted Successfully")
    
    print("Deleting Paper...")
    resp = session.delete(f"{base_url}/admin/papers/{paper_id}")
    record_api("/admin/papers/{id}", "DELETE", resp.status_code, resp.ok, env_name)
    if resp.ok:
        print_result("Paper Deleted Successfully")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_BASE_URL)
    parser.add_argument("--env", default="Local")
    args = parser.parse_args()

    success = run_simulation(args.url, args.env)
    
    print("\n" + "="*50)
    print(f"SIMULATION SUMMARY ({args.env})")
    print("="*50)
    for res in api_results:
        symbol = "✅" if res["success"] else "❌"
        print(f"{symbol} {res['method']} {res['endpoint']} -> {res['status']}")
    
    if not success:
        sys.exit(1)
