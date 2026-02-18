import requests
import uuid
import json
import time
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = f"scan_admin_{uuid.uuid4().hex[:6]}@example.com"
ADMIN_PASSWORD = "password123"
CANDIDATE_EMAIL = f"scan_candidate_{uuid.uuid4().hex[:6]}@example.com"
CANDIDATE_PASSWORD = "password123"

class EndpointScanner:
    def __init__(self):
        self.admin_session = requests.Session()
        self.candidate_session = requests.Session()
        self.errors = []
        self.endpoints_tested = 0

    def log(self, type, message):
        print(f"[{type}] {message}")

    def check(self, response, endpoint_desc, allowed_codes=[200, 201]):
        self.endpoints_tested += 1
        if response.status_code in allowed_codes:
            self.log("PASS", f"{endpoint_desc} [{response.status_code}]")
            return True
        else:
            error_msg = f"{endpoint_desc} FAILED. Status: {response.status_code}, Body: {response.text[:200]}"
            self.log("FAIL", error_msg)
            self.errors.append(error_msg)
            return False

    def setup_auth(self):
        self.log("INFO", "--- Authenticaton ---")
        
        admin_creds = [
            ("scan_super@example.com", "password123"),
            ("admin@example.com", "password123"),
            ("admin@test.com", "admin123"),
            ("admin@example.com", "password"),
            ("admin_sim@example.com", "password123"),
            (f"scan_admin_{uuid.uuid4().hex[:6]}@example.com", "password123") # Fallback: try to register new
        ]

        token = None
        for email, password in admin_creds:
            self.log("INFO", f"Attempting Admin Login with {email}...")
            resp = self.admin_session.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
            
            if resp.status_code == 200:
                token = resp.json()["data"]["access_token"]
                self.log("PASS", f"Admin Login Success ({email})")
                self.admin_session.headers.update({"Authorization": f"Bearer {token}"})
                break
            elif "scan_admin" in email:
                 # Try to register the dynamic one
                 self.log("INFO", "Admin not found, registering new dynamic admin...")
                 resp = self.admin_session.post(f"{BASE_URL}/auth/register", json={
                    "email": email, "password": password, "full_name": "Scan Admin", "role": "admin"
                 })
                 if self.check(resp, "Register Admin", allowed_codes=[200, 201]):
                     # Login after register
                     resp = self.admin_session.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
                     if resp.status_code == 200:
                         token = resp.json()["data"]["access_token"]
                         self.log("PASS", f"Admin Login Success ({email})")
                         self.admin_session.headers.update({"Authorization": f"Bearer {token}"})
                         break
            else:
                self.log("INFO", f"Login failed for {email}: {resp.status_code}")

        if not token:
            self.log("FAIL", "All Admin Login attempts failed.")
            return False

        # 2. Candidate Register
        # dynamic candidate is fine
        resp = self.admin_session.post(f"{BASE_URL}/auth/register", json={
            "email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD, "full_name": "Scan Candidate", "role": "candidate"
        })
        if self.check(resp, "Register Candidate"):
             self.candidate_id = resp.json()["data"]["id"]
        else:
             # Try to login (maybe exists?) unlikely with uuid
             return False

        # Candidate Login (to get token for candidate session)
        resp = self.candidate_session.post(f"{BASE_URL}/auth/login", json={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD})
        if self.check(resp, "Candidate Login"):
             token = resp.json()["data"]["access_token"]
             self.candidate_session.headers.update({"Authorization": f"Bearer {token}"})
        
        return True

    def scan_admin_basics(self):
        self.log("INFO", "--- Admin Basics ---")
        self.check(self.admin_session.get(f"{BASE_URL}/admin/interviews"), "List Interviews")
        self.check(self.admin_session.get(f"{BASE_URL}/admin/interviews/live-status"), "Live Status Dashboard")
        self.check(self.admin_session.get(f"{BASE_URL}/admin/papers"), "List Papers")
        self.check(self.admin_session.get(f"{BASE_URL}/admin/questions"), "List Questions")
        # Me endpoint
        self.check(self.admin_session.get(f"{BASE_URL}/auth/me"), "Admin Me Profile")

    def scan_interview_lifecycle(self):
        self.log("INFO", "--- Interview Lifecycle ---")
        
        # 1. Create Paper
        paper_data = {"name": f"Scan Paper {uuid.uuid4().hex[:4]}", "description": "Scan Test"}
        resp = self.admin_session.post(f"{BASE_URL}/admin/papers", json=paper_data)
        if not self.check(resp, "Create Paper"): return
        paper_id = resp.json()["data"]["id"]

        # 2. Add Question
        q1 = {"content": "Scan Question 1?", "topic": "Scan", "difficulty": "Easy", "marks": 10, "response_type": "text"}
        resp = self.admin_session.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", json=q1)
        self.check(resp, "Add Question")
        q_id = resp.json()["data"]["id"]

        # 3. Schedule Interview
        schedule_data = {
            "candidate_id": self.candidate_id,
            "paper_id": paper_id,
            "schedule_time": datetime.utcnow().isoformat(),
            "duration_minutes": 60,
            "max_questions": 1
        }
        resp = self.admin_session.post(f"{BASE_URL}/admin/interviews/schedule", json=schedule_data)
        if not self.check(resp, "Schedule Interview"): return
        interview_data = resp.json()["data"]["interview"]
        interview_id = interview_data["id"]
        access_token = resp.json()["data"]["access_token"]

        # 4. Access Interview (Candidate)
        # Using a fresh session for link access to simulate separate browser context, 
        # but for simplicity using candidate_session which is logged in (though link auth depends on token)
        link_session = requests.Session()
        resp = link_session.get(f"{BASE_URL}/interview/access/{access_token}")
        self.check(resp, "Access Interview Link")

        # 5. Start Session
        # Mock enrollment
        files = {"enrollment_audio": ("enroll.wav", b"dummy_wav_header", "audio/wav")}
        resp = link_session.post(f"{BASE_URL}/interview/start-session/{interview_id}", files=files)
        self.check(resp, "Start Session")

        # 6. Next Question
        resp = link_session.get(f"{BASE_URL}/interview/next-question/{interview_id}")
        self.check(resp, "Get Next Question")

        # 7. Submit Answer (Text) - Explicitly using text to avoid complex audio handling
        ans_data = {
            "interview_id": interview_id,
            "question_id": q_id,
            "answer_text": "This is a scan test answer."
        }
        resp = link_session.post(f"{BASE_URL}/interview/submit-answer-text", data=ans_data)
        self.check(resp, "Submit Text Answer")

        # 8. Finish
        resp = link_session.post(f"{BASE_URL}/interview/finish/{interview_id}")
        self.check(resp, "Finish Interview")
        
        # 9. Admin Check Result
        # Wait a moment for background processing (though text answer might be instant or async)
        time.sleep(2)
        resp = self.admin_session.get(f"{BASE_URL}/admin/results/{interview_id}")
        self.check(resp, "Get Interview Result (Admin)")

    def scan_settings(self):
        self.log("INFO", "--- Settings & System ---")
        # System status
        # Needs interview_id usually? Check schema.
        # router defines: async def get_system_status(interview_id: int):
        # We need a valid interview_id. We can use 0 or a fake one, but it might error if logic depends on it.
        # Let's try with 0
        resp = self.admin_session.get(f"{BASE_URL}/status/", params={"interview_id": 0})
        self.check(resp, "System Status Check")
        
        # Text to speech check
        resp = requests.get(f"{BASE_URL}/interview/tts", params={"text": "Hello Scan"})
        # 200 or 500? Use background_tasks, should be 200.
        self.check(resp, "Standalone TTS Check")

    def run(self):
        print("Starting Endpoint Scan (Excluding Gaze/Face Analysis)...")
        try:
            if not self.setup_auth():
                print("Critical Auth Failure. Aborting.")
                return
            
            self.scan_admin_basics()
            self.scan_interview_lifecycle()
            self.scan_settings()
            
            print("\n" + "="*50)
            print(f"Scan Complete. Tested {self.endpoints_tested} endpoints.")
            if self.errors:
                print(f"Found {len(self.errors)} Errors:")
                for e in self.errors:
                    print(f" - {e}")
            else:
                print("SUCCESS: No errors found in scanned endpoints.")
            print("="*50)

        except requests.exceptions.ConnectionError:
            print("FATAL: Could not connect to server. Is it running on port 8000?")
        except Exception as e:
            print(f"FATAL: Unexpected script error: {e}")

if __name__ == "__main__":
    scanner = EndpointScanner()
    scanner.run()
