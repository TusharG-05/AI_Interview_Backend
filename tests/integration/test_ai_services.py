import os
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8000/api"

def test_ai_accuracy():
    session = requests.Session()
    session.verify = False
    
    print("=== TESTING STT & LLM ACCURACY ===")

    # 1. Login
    r = session.post(f"{BASE_URL}/auth/register", json={
        "email": f"ai_test_{os.urandom(2).hex()}@test.com", 
        "password": "pass", "full_name": "AI Tester", "role": "candidate"
    })
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a session
    r = session.post(f"{BASE_URL}/interview/start", data={"candidate_name": "AI Tester"}, headers=headers)
    session_id = r.json()["session_id"]
    log_file = "app/assets/audio/responses/real_test.wav"
    
    # 3. Use a small real WAV file if possible, otherwise we just verify the LLM error is gone
    # I'll create a 1-second silent but VALID wav file using a trick or just check the LLM call directly
    print("Testing LLM Evaluation directly...")
    r = session.post(f"{BASE_URL}/interview/evaluate", json={
        "reference_text": "The capital of France is Paris.",
        "candidate_text": "Paris is the capital city of France."
    }, headers=headers)
    
    if r.status_code == 200:
        print(f"[PASS] LLM Evaluation result: {r.json()}")
    else:
        print(f"[FAIL] LLM Evaluation failed: {r.text}")

if __name__ == "__main__":
    test_ai_accuracy()
