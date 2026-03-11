import requests
import json
import time

BASE_URL = "https://ichigo253-ai-interview-backend.hf.space/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def print_result(name, success, data=None):
    print(f"\n{'✅ PASS' if success else '❌ FAIL'} | {name}")
    if data:
        print(f"Details: {data}")

def run_tests():
    print("🚀 Starting Live Groq LLM Endpoint Tests on HF v1...")

    # 1. Login
    print("\n[1] Authenticating as Admin...")
    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}
    )
    if login_res.status_code != 200:
        print_result("Admin Login", False, login_res.text)
        return
    
    data = login_res.json().get("data", {})
    token = data.get("access_token")
    if not token:
        print_result("Admin Login", False, f"Token not found in response: {login_res.text}")
        return
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated successfully.")

    # 2. Test Question Generation (Groq)
    print("\n[2] Testing Question Generation (/api/admin/generate-paper)...")
    prompt = "FastAPI and Python basics"
    start_time = time.time()
    gen_res = requests.post(
        f"{BASE_URL}/admin/generate-paper",
        headers=headers,
        json={
            "ai_prompt": prompt, 
            "num_questions": 2,
            "years_of_experience": "2",
            "team_id": 1
        }
    )
    gen_time = time.time() - start_time
    
    if gen_res.status_code == 201:
        data = gen_res.json()
        questions = data.get("data", {}).get("questions", [])
        print_result(f"Generate Paper ({gen_time:.2f}s)", True, f"Generated {len(questions)} questions on '{prompt}'.")
        for i, q in enumerate(questions):
            print(f"  Q{i+1}: {q.get('question_text')}")
    else:
        print_result("Generate Paper", False, gen_res.text)

    # 3. Test Answer Evaluation (Groq)
    print("\n[3] Testing Answer Evaluation (/api/interview/evaluate-answer)...")
    eval_payload = {
        "question": "What is the primary purpose of FastAPI's dependency injection system?",
        "answer": "It allows you to share logic, database connections, and enforce security across multiple endpoints cleanly without repeating code."
    }
    
    start_time = time.time()
    eval_res = requests.post(
        f"{BASE_URL}/interview/evaluate-answer",
        headers=headers,
        json=eval_payload
    )
    eval_time = time.time() - start_time
    
    if eval_res.status_code == 200:
        data = eval_res.json().get("data", {})
        print_result(f"Evaluate Answer ({eval_time:.2f}s)", True)
        print(f"  Score: {data.get('score')}/10")
        print(f"  Feedback: {data.get('feedback')}")
    else:
        print_result("Evaluate Answer", False, eval_res.text)
        
if __name__ == "__main__":
    run_tests()
