import httpx
import os
import json
import time
import asyncio
from typing import Dict, Any
from sqlmodel import Session, select, create_engine
from datetime import datetime, timezone, timedelta

# Import DB Models for setup
import sys
sys.path.append(os.getcwd())
from app.core.database import engine
from app.models.db_models import User, InterviewSession, InterviewStatus, Questions, QuestionPaper

BASE_URL = "http://127.0.0.1:7860/api"

class AuditReporter:
    def __init__(self):
        self.results = []

    def log(self, section: str, endpoint: str, success: bool, payload: str, response: str):
        self.results.append({
            "section": section,
            "endpoint": endpoint,
            "success": success,
            "payload": payload,
            "response": response
        })

    def print_summary(self):
        print("\n" + "="*80)
        print("EXHAUSTIVE API AUDIT RESULTS")
        print("="*80)
        for r in self.results:
            status = "✅ PASS" if r["success"] else "❌ FAIL"
            print(f"{status} | {r['section']} - {r['endpoint']}")
            # print(f"Response: {r['response'][:100]}...")
        print("="*80)

    def print_detailed_outputs(self):
        print("\n" + "="*80)
        print("DETAILED RESPONSE OUTPUTS")
        print("="*80)
        for r in self.results:
            status = "✅ PASS" if r["success"] else "❌ FAIL"
            print(f"\n[{r['section']}] {r['endpoint']} -> {status}")
            print(f"Payload: {r['payload']}")
            print(f"Response Body:")
            if r['response'].startswith('{') or r['response'].startswith('['):
                try:
                    print(json.dumps(json.loads(r['response']), indent=2))
                except:
                    print(r['response'])
            else:
                print(r['response'])
        print("="*80)

async def test_all_apis():
    reporter = AuditReporter()
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. System Health
        print("\n[Section 1] System Status...")
        resp = await client.get(f"{BASE_URL}/status/")
        reporter.log("System", "GET /status/", resp.status_code == 200, "None", resp.text)

        # 2. Auth Flow
        print("[Section 2] Auth Operations...")
        test_email = f"audit_user_{int(time.time())}@example.com"
        reg_payload = {"email": test_email, "password": "auditpassword", "full_name": "Audit User"}
        
        # Insert user manually to bypass Admin-only registration checks
        try:
            from app.auth.security import get_password_hash
            from app.models.db_models import UserRole
            with Session(engine) as db:
                new_user = User(
                    email=test_email,
                    full_name="Audit User",
                    password_hash=get_password_hash("auditpassword"),
                    role=UserRole.ADMIN
                )
                db.add(new_user)
                db.commit()
                reporter.log("Auth", "(Manual User Injection)", True, "None", "User created via DB")
        except Exception as e:
            reporter.log("Auth", "(Manual User Injection)", False, "None", f"Error: {e}")
        
        # Register (Will likely fail due to admin restriction, this is expected)
        resp = await client.post(f"{BASE_URL}/auth/register", json=reg_payload)
        reporter.log("Auth", "POST /auth/register", resp.status_code in [200, 201, 403], json.dumps(reg_payload), resp.text)
        
        # Login
        login_data = {"email": test_email, "password": "auditpassword"}
        resp = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        token = ""
        if resp.status_code == 200:
            token = resp.json().get("data", {}).get("access_token")
            reporter.log("Auth", "POST /auth/login", True, json.dumps(login_data), resp.text)
        else:
            reporter.log("Auth", "POST /auth/login", False, json.dumps(login_data), resp.text)
            return reporter

        headers = {"Authorization": f"Bearer {token}"}
        
        # Profile
        resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        reporter.log("Auth", "GET /auth/me", resp.status_code == 200, "None", resp.text)
        user_id = resp.json().get("data", {}).get("id") if resp.status_code == 200 else 1

        # 3. Create Mock Infrastructure for Interview Testing
        print("[Section 3] Setting up Mock Interview Session...")
        int_id = None
        q_id = None
        try:
            with Session(engine) as db:
                # Create Paper
                paper = QuestionPaper(name="Audit Paper", admin_id=user_id, total_marks=100)
                db.add(paper)
                db.commit(); db.refresh(paper)
                
                # Create Questions
                q1 = Questions(paper_id=paper.id, content="Explain Recursion", marks=10, difficulty="easy", response_type="text")
                q2 = Questions(paper_id=paper.id, content="Write a fizzbuzz function", marks=10, difficulty="medium", response_type="code")
                db.add(q1); db.add(q2)
                db.commit(); db.refresh(q1); db.refresh(q2)
                
                # Create Session
                interview_session = InterviewSession(
                    candidate_id=user_id, paper_id=paper.id, status=InterviewStatus.SCHEDULED,
                    access_token=f"audit_token_{int(time.time())}", 
                    duration_minutes=60, schedule_time=datetime.now(timezone.utc)
                )
                db.add(interview_session)
                db.commit(); db.refresh(interview_session)
                int_id = interview_session.id
                q_id = q1.id
        except Exception as e:
            print(f"Error setting up database: {e}")

        # 4. Interview Workflow
        print("[Section 4] Interview Workflow...")
        if int_id and q_id:
            # Submit Text
            text_ans = {"interview_id": int_id, "question_id": q_id, "answer_text": "Recursion is a process in which a function calls itself."}
            resp = await client.post(f"{BASE_URL}/interview/submit-answer-text", data=text_ans, headers=headers)
            reporter.log("Interview", "POST /submit-answer-text", resp.status_code == 200, json.dumps(text_ans), resp.text)

        # Evaluate Answer (Stateless)
        eval_ans = {"question": "What is Python?", "answer": "A high-level programming language."}
        resp = await client.post(f"{BASE_URL}/interview/evaluate-answer", json=eval_ans, headers=headers)
        reporter.log("Interview", "POST /evaluate-answer", resp.status_code == 200, json.dumps(eval_ans), resp.text)

        # STT Tool
        audio_path = "tests/assets/test_audio.mp3"
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                files = {"audio": (os.path.basename(audio_path), f, "audio/mpeg")}
                resp = await client.post(f"{BASE_URL}/interview/tools/speech-to-text", files=files, headers=headers)
                reporter.log("InterviewTools", "POST /tools/speech-to-text", resp.status_code == 200, "AudioFile", resp.text)
        else:
            reporter.log("InterviewTools", "POST /tools/speech-to-text", False, "AudioFile", f"File not found: {audio_path}")

        # TTS Tool
        resp = await client.get(f"{BASE_URL}/interview/tts", params={"text": "Audit complete."}, headers=headers, follow_redirects=True)
        reporter.log("InterviewTools", "GET /tts", resp.status_code in [200, 307], "text=Audit complete.", f"Status: {resp.status_code}, URL={resp.url}")

        # 5. Candidate APIs
        print("[Section 5] Candidate APIs...")
        resp = await client.get(f"{BASE_URL}/candidate/history", headers=headers)
        reporter.log("Candidate", "GET /candidate/history", resp.status_code == 200, "None", resp.text)
        
        resp = await client.get(f"{BASE_URL}/candidate/interviews", headers=headers)
        reporter.log("Candidate", "GET /candidate/interviews", resp.status_code == 200, "None", resp.text)

        # Selfie Upload
        img_path = "tests/assets/test_face.jpg"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                files = {"file": ("selfie.jpg", f, "image/jpeg")}
                resp = await client.post(f"{BASE_URL}/candidate/upload-selfie", files=files, headers=headers)
                reporter.log("Candidate", "POST /upload-selfie", resp.status_code == 200, "ImageFile", resp.text)
        else:
            reporter.log("Candidate", "POST /upload-selfie", False, "ImageFile", f"File not found: {img_path}")

        # 6. Session Completion
        if int_id:
            print("[Section 6] Finalizing Session...")
            resp = await client.post(f"{BASE_URL}/interview/finish/{int_id}", headers=headers)
            reporter.log("Interview", f"POST /finish/{int_id}", resp.status_code == 200, "None", resp.text)

        return reporter

if __name__ == "__main__":
    rep = asyncio.run(test_all_apis())
    rep.print_detailed_outputs()
    rep.print_summary()
