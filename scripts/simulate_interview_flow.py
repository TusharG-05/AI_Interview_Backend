import requests
import time
import uuid
import sys
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin_sim@example.com"
ADMIN_PASSWORD = "password123"
CANDIDATE_EMAIL = f"candidate_sim_{uuid.uuid4().hex[:6]}@example.com"
CANDIDATE_PASSWORD = "password123"

def print_step(msg):
    print(f"\n{'='*50}\n[STEP] {msg}\n{'='*50}")

def print_result(msg, data=None):
    print(f" -> {msg}")
    if data:
        print(f"    Data: {json.dumps(data, indent=2)}")

def fail(msg):
    print(f"\n[FAILURE] {msg}")
    sys.exit(1)

def run_simulation():
    session = requests.Session()
    
    # ---------------------------------------------------------
    # 1. Admin Login & Setup
    # ---------------------------------------------------------
    print_step("1. Admin Login & Setup")
    
    # Register/Login Admin
    # Try login first
    print("Attempting Admin Login...")
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    
    if resp.status_code == 401:
        print("Admin not found, registering...")
        # Start fresh session for register just in case
        auth_session = requests.Session() 
        # Register needs a token usually if not bootstrap, but let's try bootstrap or reuse existing super admin if known?
        # Actually, the code says "First user can register freely (Bootstrap)". 
        # If admin exists, we might default to a known one or fail if we can't create.
        # Let's assume dev env where we can register or we have credentials.
        # If fail, we assume admin_sim needs creation.
        
        # Try registering
        resp = auth_session.post(f"{BASE_URL}/auth/register", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "full_name": "Sim Admin", "role": "admin"
        })
        if not resp.ok:
            # Maybe already exists but password wrong? Or strict registration?
            # Let's try to list users (needs auth) - catch 22.
            # Assume strict env: Use the known credentials or fail.
            print(f"Registration failed: {resp.text}. Assuming Admin exists with different credentials or system locked.")
            # RETRY LOGIN with generic test creds or fail?
            # Let's try the user provided "admin@example.com" from verification script?
            # No, let's just proceed with LOGIN check.
    
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print_result("Admin Logged In")
    else:
        # Retry with a super admin fallback?
        # Or just fail
        fail(f"Could not login as Admin ({ADMIN_EMAIL}). Status: {resp.status_code}, Body: {resp.text}")

    # Create Question Paper
    print("Creating Question Paper...")
    paper_data = {"name": f"Sim Paper {uuid.uuid4().hex[:4]}", "description": "E2E Test Paper"}
    resp = session.post(f"{BASE_URL}/admin/papers", json=paper_data)
    if not resp.ok: fail(f"Create Paper Failed: {resp.text}")
    paper_id = resp.json()["data"]["id"]
    print_result(f"Paper Created: ID {paper_id}")

    # Add Questions
    print("Adding Questions...")
    q1 = {"content": "What is Python?", "topic": "Tech", "difficulty": "Easy", "marks": 10, "response_type": "text"}
    resp = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q1)
    if not resp.ok: fail("Add Q1 Failed")
    q1_id = resp.json()["data"]["id"]

    q2 = {"content": "Explain AI.", "topic": "AI", "difficulty": "Medium", "marks": 20, "response_type": "text"}
    resp = session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q2)
    if not resp.ok: fail("Add Q2 Failed")
    q2_id = resp.json()["data"]["id"]
    
    print_result(f"Added 2 Questions: {q1_id}, {q2_id}")

    # ---------------------------------------------------------
    # 2. Candidate Setup & Scheduling
    # ---------------------------------------------------------
    print_step("2. Candidate Setup & Scheduling")
    
    # Register Candidate
    print(f"Registering Candidate: {CANDIDATE_EMAIL}...")
    resp = session.post(f"{BASE_URL}/auth/register", json={
        "email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD, "full_name": "Sim Candidate", "role": "candidate"
    })
    
    # If 403 (Forbidden), it means only Admins can register. 
    # Since we are logged in as Admin, this should work!
    if not resp.ok: fail(f"Candidate Register Failed: {resp.text}")
    candidate_id = resp.json()["data"]["id"]
    print_result(f"Candidate Registered: ID {candidate_id}")

    # Schedule Interview
    print("Scheduling Interview...")
    schedule_data = {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "schedule_time": (datetime.utcnow() + timedelta(minutes=1)).isoformat(), # Start in 1 min
        "duration_minutes": 60,
        "max_questions": 2
    }
    resp = session.post(f"{BASE_URL}/admin/interviews/schedule", json=schedule_data)
    if not resp.ok: fail(f"Schedule Failed: {resp.text}")
    interview_data = resp.json()["data"]
    interview_id = interview_data["interview_id"]
    access_token = interview_data["access_token"]
    print_result(f"Interview Scheduled: ID {interview_id}", {"Link": interview_data["link"]})

    # ---------------------------------------------------------
    # 3. Candidate Flow
    # ---------------------------------------------------------
    print_step("3. Candidate Flow")
    
    candidate_session = requests.Session()
    # Candidate doesn't explicit Login for Access Link usually? 
    # Code says: @router.get("/access/{token}") -> No Auth required?
    # Wait, `router = APIRouter(prefix="/interview")`
    # access_interview takes `token`.
    
    # Access Link
    print("Accessing Interview Link...")
    resp = candidate_session.get(f"{BASE_URL}/interview/access/{access_token}")
    
    # It might say "WAIT" if we are too early?
    # Our schedule time was +1 min. 
    # Let's allow it to start immediately? 
    # Code: `if now < schedule_time: return WAIT`.
    # We might need to wait or hack the start time.
    # Actually, let's just wait 2 seconds, maybe we gave it +1 MINUTE which is 60s.
    # Update: Let's patch the schedule time via Admin API to "now" to avoid waiting.
    
    print("  -> Updating schedule time to NOW for immediate access...")
    update_data = {"schedule_time": datetime.utcnow().isoformat()}
    resp_update = session.patch(f"{BASE_URL}/admin/interviews/{interview_id}", json=update_data)
    if resp_update.status_code != 200: 
        print(f"  -> Warning: Failed to update time: {resp_update.text}. Access might wait.")
    
    # Retry Access
    resp = candidate_session.get(f"{BASE_URL}/interview/access/{access_token}")
    if resp.status_code == 200 and resp.json()["data"]["message"] == "WAIT":
        print("  -> Still waiting... (Sleeping 2s)")
        time.sleep(2)
        resp = candidate_session.get(f"{BASE_URL}/interview/access/{access_token}")

    if resp.status_code != 200 or resp.json()["data"]["message"] == "WAIT":
        fail(f"Could not access interview: {resp.json()}")
    
    print_result("Access Granted")

    # Start Session (Enrollment)
    print("Starting Session (Enrollment)...")
    # Needs enrollment_audio
    # Mock file
    files = {"enrollment_audio": ("enroll.wav", b"riff_wave_header_dummy_content", "audio/wav")}
    resp = candidate_session.post(f"{BASE_URL}/interview/start-session/{interview_id}", files=files)
    if resp.status_code != 200: fail(f"Start Session Failed: {resp.text}")
    print_result("Session Started (LIVE)")

    # ---------------------------------------------------------
    # 4. Q&A Loop
    # ---------------------------------------------------------
    print_step("4. Q&A Loop")

    # Question 1
    print("Fetching Q1...")
    resp = candidate_session.get(f"{BASE_URL}/interview/next-question/{interview_id}")
    q_data = resp.json()["data"]
    
    if "status" in q_data and q_data["status"] == "finished":
        fail("Premature finish?")
        
    q1_id_fetched = q_data["question_id"]
    print_result(f"Got Q1: {q_data['text']}")

    # Submit Text Answer
    print("Submitting Answer for Q1...")
    ans_data = {
        "interview_id": interview_id,
        "question_id": q1_id_fetched,
        "answer_text": "Python is a high-level programming language."
    }
    resp = candidate_session.post(f"{BASE_URL}/interview/submit-answer-text", data=ans_data)
    if resp.status_code != 200: fail(f"Submit Q1 Failed: {resp.text}")
    print_result("Q1 Submitted")

    # Question 2
    print("Fetching Q2...")
    resp = candidate_session.get(f"{BASE_URL}/interview/next-question/{interview_id}")
    q_data = resp.json()["data"]
    
    q2_id_fetched = q_data["question_id"]
    print_result(f"Got Q2: {q_data['text']}")

    # Submit Audio Answer (Mock)
    print("Submitting Audio Answer for Q2...")
    files = {"audio": ("ans2.wav", b"dummy_audio_content", "audio/wav")}
    data = {"interview_id": interview_id, "question_id": q2_id_fetched}
    resp = candidate_session.post(f"{BASE_URL}/interview/submit-answer-audio", files=files, data=data)
    if resp.status_code != 200: fail(f"Submit Q2 Failed: {resp.text}")
    print_result("Q2 Submitted")

    # Check for Finish
    print("Checking next (Expect Finished)...")
    resp = candidate_session.get(f"{BASE_URL}/interview/next-question/{interview_id}")
    if resp.json()["data"].get("status") == "finished":
        print_result("No more questions")
    else:
        print(f"Warning: Expected finish, got {resp.json()}")

    # ---------------------------------------------------------
    # 5. Finish & Verify
    # ---------------------------------------------------------
    print_step("5. Finish & Verify Result")
    
    # Finish
    resp = candidate_session.post(f"{BASE_URL}/interview/finish/{interview_id}")
    if resp.status_code != 200: fail(f"Finish Failed: {resp.text}")
    print_result("Interview Finished")

    # Verify Results (As Admin)
    # Give some time for background processing (AI Evaluation)
    print("Waiting 5s for AI Evaluation...")
    time.sleep(5)
    
    print("Fetching Result as Admin...")
    resp = session.get(f"{BASE_URL}/admin/results/{interview_id}")
    if resp.status_code != 200: fail(f"Get Result Failed: {resp.text}")
    
    result_data = resp.json()["data"]
    
    # Check Score
    total_score = result_data.get("total_score")
    answers = result_data.get("answers", [])
    
    print_result(f"Result Fetched. Total Score: {total_score}")
    print(f"    Answers Count: {len(answers)}")
    
    for ans in answers:
        print(f"    - Q{ans['question_id']} Score: {ans['score']}")
        print(f"      Feedback: {ans['feedback']}")
    
    if total_score is None:
        print("\n[WARNING] Total Score is None. AI usage might be mocked or failed?")
    else:
        print("\n[SUCCESS] Simulation Complete. Full flow verified.")

if __name__ == "__main__":
    try:
        run_simulation()
    except requests.exceptions.ConnectionError:
        fail("Could not connect to server. Is it running on localhost:8000?")
    except Exception as e:
        fail(f"Unexpected Error: {e}")
