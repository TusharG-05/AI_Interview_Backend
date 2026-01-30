import requests
import json
import os

# Configuration
BASE_URL = os.getenv("API_URL", "https://localhost:8000/api")
if not BASE_URL.endswith("/api"):
    BASE_URL += "/api"

AUTH_URL = f"{BASE_URL}/auth"
ADMIN_URL = f"{BASE_URL}/admin"
CANDIDATE_URL = f"{BASE_URL}/candidate"
INTERVIEW_URL = f"{BASE_URL}/interview"
VERIFY_SSL = False # Local testing with self-signed certs

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, status=True):
    color = GREEN if status else RED
    mark = "[PASS]" if status else "[FAIL]"
    print(f"{color}{mark} {msg}{RESET}")

def run_tests():
    session = requests.Session()
    session.verify = VERIFY_SSL
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    admin_token = ""
    candidate_token = ""
    room_code = ""
    room_password = ""
    session_id = 0
    
    print("=== STARTING API AUDIT ===")

    # 1. Health Check
    try:
        r = session.get(f"{BASE_URL}/status/")
        if r.status_code == 200: log("System Health Check")
        else: log(f"System Health Check ({r.status_code})", False)
    except Exception as e:
        log(f"System Down: {e}", False)
        return

    # 2. Admin Register/Login
    admin_email = f"admin_audit_{os.urandom(4).hex()}@test.com"
    r = session.post(f"{AUTH_URL}/register", json={
        "email": admin_email, "password": "password123", "full_name": "Audit Admin", "role": "admin"
    })
    if r.status_code == 200: 
        log("Admin Registration")
        admin_token = r.json()["access_token"]
    else: log(f"Admin Registration Failed: {r.text}", False)

    # 3. Create Room (Admin)
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = session.post(f"{ADMIN_URL}/rooms", json={"password": "roompass", "max_sessions": 10}, headers=headers)
    if r.status_code == 200:
        data = r.json()
        room_code = data["room_code"]
        room_password = data["password"]
        log(f"Create Room ({room_code})")
    else: log(f"Create Room Failed: {r.text}", False)

    # 4. Add Question (Admin)
    r = session.post(f"{ADMIN_URL}/questions", json={
        "content": "Explain Dependency Injection.", "topic": "Architecture", "difficulty": "Hard"
    }, headers=headers)
    if r.status_code == 200: log("Add Question")
    else: log("Add Question Failed", False)

    # 5. Candidate Register
    cand_email = f"cand_audit_{os.urandom(4).hex()}@test.com"
    r = session.post(f"{AUTH_URL}/register", json={
        "email": cand_email, "password": "password123", "full_name": "Audit Candidate", "role": "candidate"
    })
    if r.status_code == 200:
        log("Candidate Registration")
        candidate_token = r.json()["access_token"]
    else: log("Candidate Registration Failed", False)

    cand_headers = {"Authorization": f"Bearer {candidate_token}"}

    # 6. Upload Selfie
    # Create dummy image if empty
    with open("tools/test_assets/selfie.jpg", "wb") as f: f.write(b"fake_image_bytes")
    
    files = {"file": ("selfie.jpg", open("tools/test_assets/selfie.jpg", "rb"), "image/jpeg")}
    r = session.post(f"{CANDIDATE_URL}/upload-selfie", files=files, headers=cand_headers)
    if r.status_code == 200: log("Upload Selfie")
    else: log(f"Upload Selfie Failed: {r.text}", False)

    # 7. Join Room
    r = session.post(f"{CANDIDATE_URL}/join", json={"room_code": room_code, "password": room_password}, headers=cand_headers)
    if r.status_code == 200:
        log("Join Room")
        session_id = r.json()["session_id"]
    else: log(f"Join Room Failed: {r.text}", False)

    # 8. Start Interview (Voice Auth Enroll)
    # Dummy Start with audio
    files = {
        "candidate_name": (None, "Audit Cand"),
        "enrollment_audio": ("enroll.wav", b"fake_audio", "audio/wav")
    }
    # Note: Logic might fail if audio is too short/fake for energy check, but API structure check matters here
    r = session.post(f"{INTERVIEW_URL}/start", files=files, headers=cand_headers) # Start session is weird, it re-creates session or updates? 
    # Actually, start endpoint creates a NEW session. But we joined a room earlier. 
    # In current Candidate flow, 'Join' creates session. 'Start' updates it? 
    # Let's check logic: 'start' endpoint creates NEW Session. 'join' endpoint creates NEW Session.
    # This identifies a LOGIC CLASH.
    if r.status_code == 200: log("Start Interview API (Legacy?)")
    else: log(f"Start Interview Failed: {r.text}", False)

    # 9. Get Next Question
    # Using session_id from JOIN
    r = session.get(f"{INTERVIEW_URL}/next-question/{session_id}", headers=cand_headers)
    if r.status_code == 200: 
        q_data = r.json()
        log(f"Get Next Question ({q_data.get('text', 'FINISHED')})")
    else: log(f"Get Next Question Failed: {r.text}", False)

    # 10. Admin Dashboard
    r = session.get(f"{ADMIN_URL}/users/results", headers=headers)
    if r.status_code == 200: log("Admin Dashboard Stats")
    else: log("Admin Dashboard Failed", False)

    print("=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    run_tests()
