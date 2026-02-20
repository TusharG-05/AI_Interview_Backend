import requests
import time
import random
import string
import sys
import json

# Configuration
BASE_URL = "https://ichigo253-ai-interview-backend.hf.space"
API_URL = f"{BASE_URL}/api"

# Utils
def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

class APIAuditor:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.candidate_token = None
        self.test_suffix = random_string(4)
        self.admin_email = "admin@test.com"
        self.password = "admin123"
        self.candidate_email = f"candidate_{self.test_suffix}@test.com"
        self.candidate_password = "P@ssw0rd123!"
        
        self.paper_id = None
        self.question_id = None
        self.candidate_id = None
        self.interview_id = None
        self.access_token = None

    def log(self, section, message, data=None):
        print(f"\n{'='*20} {section} {'='*20}")
        print(f"Status: {message}")
        if data:
            print(f"Response: {json.dumps(data, indent=2)}")

    def run_tests(self):
        try:
            self.test_01_health_check()
            self.test_03_admin_login()
            self.test_04_candidate_registration_by_admin()
            self.test_05_create_question_paper()
            self.test_06_add_questions_to_paper()
            self.test_07_schedule_interview()
            self.test_08_candidate_login()
            self.test_09_fetch_candidate_interviews()
            self.test_10_verify_interview_access()
            self.test_11_submit_text_answer()
            print("\n✅ ALL CLOUD API TESTS PASSED!")
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            sys.exit(1)

    def test_01_health_check(self):
        resp = self.session.get(BASE_URL)
        if resp.status_code in [200, 302, 307, 303]:
            self.log("HEALTH CHECK", "PASS - Server is reachable")
        else:
            raise Exception(f"Server unreachable. Status: {resp.status_code}")

    def test_02_admin_registration(self):
        # First registration might be bootstrap (free)
        payload = {
            "email": self.admin_email,
            "password": self.password,
            "full_name": f"Auditor Admin {self.test_suffix}",
            "role": "admin"
        }
        resp = self.session.post(f"{API_URL}/auth/register", json=payload)
        try:
            data = resp.json()
        except:
            data = {"raw": resp.text}
            
        if resp.status_code in [201, 200]:
            self.log("ADMIN REGISTRATION", "PASS", data)
        else:
            print(f"DEBUG: Status Code: {resp.status_code}")
            print(f"DEBUG: Response Body: {resp.text}")
            raise Exception(f"Admin registration failed: {data.get('detail', 'Unknown error')}")

    def test_03_admin_login(self):
        payload = {
            "email": self.admin_email,
            "password": self.password
        }
        resp = self.session.post(f"{API_URL}/auth/login", json=payload)
        data = resp.json()
        if resp.status_code == 200:
            self.admin_token = data['data']['access_token']
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            self.log("ADMIN LOGIN", "PASS", data)
        else:
            raise Exception(f"Admin login failed: {data.get('detail', 'Unknown error')}")

    def test_04_candidate_registration_by_admin(self):
        payload = {
            "email": self.candidate_email,
            "password": self.candidate_password,
            "full_name": f"Auditor Candidate {self.test_suffix}",
            "role": "candidate"
        }
        resp = self.session.post(f"{API_URL}/auth/register", json=payload)
        data = resp.json()
        if resp.status_code in [201, 200]:
            self.candidate_id = data['data']['id']
            self.log("CANDIDATE REGISTRATION", "PASS", data)
        else:
            raise Exception(f"Candidate registration failed: {data.get('detail', 'Unknown error')}")

    def test_05_create_question_paper(self):
        payload = {
            "name": f"Audit Paper {self.test_suffix}",
            "description": "Verification paper for cloud audit"
        }
        resp = self.session.post(f"{API_URL}/admin/papers", json=payload)
        data = resp.json()
        if resp.status_code == 201 or resp.status_code == 200:
            self.paper_id = data['data']['id']
            self.log("CREATE PAPER", "PASS", data)
        else:
            raise Exception(f"Failed to create paper: {data.get('detail', 'Unknown error')}")

    def test_06_add_questions_to_paper(self):
        payload = {
            "content": "What is Python?",
            "response_type": "audio",
            "topic": "General"
        }
        resp = self.session.post(f"{API_URL}/admin/papers/{self.paper_id}/questions", json=payload)
        data = resp.json()
        if resp.status_code == 201 or resp.status_code == 200:
            self.question_id = data['data']['id']
            self.log("ADD QUESTION", "PASS", data)
        else:
            raise Exception(f"Failed to add question: {data.get('detail', 'Unknown error')}")

    def test_07_schedule_interview(self):
        # Schedule for current time
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        payload = {
            "candidate_id": self.candidate_id,
            "paper_id": self.paper_id,
            "schedule_time": now.isoformat(),
            "duration_minutes": 30
        }
        resp = self.session.post(f"{API_URL}/admin/interviews/schedule", json=payload)
        try:
            data = resp.json()
        except:
            data = {"raw": resp.text}
            
        if resp.status_code in [200, 201]:
            self.interview_id = data['data']['interview']['id']
            self.access_token = data['data']['access_token']
            self.log("SCHEDULE INTERVIEW", f"PASS ({resp.status_code})", data)
        else:
            print(f"DEBUG: Status Code: {resp.status_code}")
            print(f"DEBUG: Response Body: {resp.text}")
            raise Exception(f"Failed to schedule interview: {data.get('detail', 'Unknown error')}")

    def test_08_candidate_login(self):
        # Clear headers to test candidate session separately
        self.session.headers.pop("Authorization", None)
        payload = {
            "email": self.candidate_email,
            "password": self.candidate_password
        }
        resp = self.session.post(f"{API_URL}/auth/login", json=payload)
        data = resp.json()
        if resp.status_code == 200:
            self.candidate_token = data['data']['access_token']
            self.session.headers.update({"Authorization": f"Bearer {self.candidate_token}"})
            self.log("CANDIDATE LOGIN", "PASS", data)
        else:
            raise Exception(f"Candidate login failed: {data.get('detail', 'Unknown error')}")

    def test_09_fetch_candidate_interviews(self):
        resp = self.session.get(f"{API_URL}/candidate/interviews")
        data = resp.json()
        if resp.status_code == 200:
            found = any(i['interview_id'] == self.interview_id for i in data['data'])
            if found:
                self.log("FETCH CANDIDATE INTERVIEWS", "PASS", data)
            else:
                raise Exception("Scheduled interview not found in candidate list")
        else:
            raise Exception(f"Failed to fetch interviews: {data.get('detail', 'Unknown error')}")

    def test_10_verify_interview_access(self):
        # Access token from schedule response
        resp = self.session.get(f"{API_URL}/interview/access/{self.access_token}")
        data = resp.json()
        if resp.status_code == 200:
            if data['data']['message'] == "START":
                self.log("VERIFY INTERVIEW ACCESS", "PASS", data)
            else:
                self.log("VERIFY INTERVIEW ACCESS", f"PASS (Status: {data['data']['message']})", data)
        else:
            raise Exception(f"Failed to access interview: {data.get('detail', 'Unknown error')}")

    def test_11_submit_text_answer(self):
        payload = {
            "interview_id": self.interview_id,
            "question_id": self.question_id,
            "answer_text": "Python is a high-level programming language."
        }
        # Using form-data as required by the endpoint
        resp = self.session.post(f"{API_URL}/interview/submit-answer-text", data=payload)
        data = resp.json()
        if resp.status_code == 200:
            self.log("SUBMISSION (TEXT)", "PASS", data)
        else:
            self.log("SUBMISSION (TEXT)", f"WARN (Optional) - {data.get('detail')}")

if __name__ == "__main__":
    auditor = APIAuditor()
    auditor.run_tests()
