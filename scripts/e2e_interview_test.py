import requests
import json
import time
import os

BASE_URL = "https://ichigo253-ai-interview-backend.hf.space/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"
CANDIDATE_EMAIL = "tushar@chicmicstudios.in"
CANDIDATE_PASS = "tush#4184"

# Get absolute path for assets regardless of where script is run
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DUMMY_FACE = os.path.join(PROJECT_ROOT, "dummy_face.png")
DUMMY_AUDIO = os.path.join(PROJECT_ROOT, "dummy_audio.wav")
TIMEOUT = 120 # High timeout for HF

def log_response(response, title):
    print(f"\n[{time.strftime('%H:%M:%S')}] === {title} ===")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    except:
        print(f"Raw Output: {response.text[:500]}...")
        return None

def run_test():
    total_start = time.time()
    
    # 1. Admin Login
    print("Step 1: Admin Login...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=TIMEOUT)
    data = log_response(resp, "Admin Login")
    admin_token = data["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Add/Find Candidate
    print("\nStep 2: Adding/Finding Candidate...")
    candidate_id = None
    
    if os.path.exists(DUMMY_FACE):
        with open(DUMMY_FACE, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/admin/users",
                headers=headers,
                data={
                    "email": CANDIDATE_EMAIL,
                    "full_name": "Tushar Candidate",
                    "password": CANDIDATE_PASS,
                    "role": "CANDIDATE"
                },
                files={"profile_image": f},
                timeout=TIMEOUT
            )
        data = log_response(resp, "Add Candidate")
        if data and data.get("success"):
            candidate_id = data["data"]["id"]
    
    if not candidate_id:
        print("Finding existing candidate by email...")
        users_resp = requests.get(f"{BASE_URL}/admin/users", headers=headers, timeout=TIMEOUT)
        users_data = users_resp.json().get("data", [])
        for user in users_data:
            if user["email"].lower() == CANDIDATE_EMAIL.lower():
                candidate_id = user["id"]
                print(f"Found existing candidate! ID: {candidate_id}")
                break
    
    if not candidate_id:
        print("Error: Could not find or create candidate. Aborting.")
        return

    # 3. Create Text Paper
    print("\nStep 3: Creating Text Paper...")
    paper_resp = requests.post(
        f"{BASE_URL}/admin/papers",
        headers=headers,
        json={"name": "Python Interview Paper", "description": "Assessment with 2 text questions"},
        timeout=TIMEOUT
    )
    data = log_response(paper_resp, "Create Text Paper")
    paper_id = data["data"]["id"]

    # 4. Add Text Questions
    print("\nStep 4: Adding 2 Text Questions...")
    questions = [
        {"content": "Explain decorators in Python.", "topic": "Python", "marks": 5, "response_type": "text"},
        {"content": "How does FastAPI handle asynchronous requests?", "topic": "FastAPI", "marks": 5, "response_type": "text"}
    ]
    for q in questions:
        requests.post(f"{BASE_URL}/admin/papers/{paper_id}/questions", headers=headers, json=q, timeout=TIMEOUT)

    # 5. Create Coding Paper
    print("\nStep 5: Generating Coding Paper...")
    coding_resp = requests.post(
        f"{BASE_URL}/admin/generate-coding-paper",
        headers=headers,
        json={
            "ai_prompt": "Binary Tree Inorder Traversal",
            "difficulty_mix": "medium",
            "num_questions": 1,
            "paper_name": "Tree Algorithms"
        },
        timeout=TIMEOUT
    )
    data = log_response(coding_resp, "Create Coding Paper")
    coding_paper_id = data["data"]["id"]

    # 6. Schedule Interview
    print("\nStep 6: Scheduling Interview...")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    schedule_data = {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "coding_paper_id": coding_paper_id,
        "schedule_time": now,
        "duration_minutes": 60,
        "interview_round": "ROUND_1"
    }
    try:
        sch_resp = requests.post(f"{BASE_URL}/admin/interviews/schedule", headers=headers, json=schedule_data, timeout=TIMEOUT)
        data = log_response(sch_resp, "Schedule Interview")
        access_token = data["data"]["access_token"]
        interview_id = data["data"]["interview"]["id"]
    except Exception as e:
        print(f"Schedule Interview Error: {e}")
        return

    # 7. Candidate Login
    print("\nStep 7: Candidate Login...")
    try:
        cand_login_resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASS, "access_token": access_token},
            timeout=TIMEOUT
        )
        data = log_response(cand_login_resp, "Candidate Login")
        cand_token = data["data"]["access_token"]
        cand_headers = {"Authorization": f"Bearer {cand_token}"}
    except Exception as e:
        print(f"Candidate Login Error: {e}")
        return

    # 8. Start Session
    print("\nStep 8: Starting Interview Session...")
    requests.post(f"{BASE_URL}/interview/start-session/{interview_id}", headers=cand_headers, timeout=TIMEOUT)

    # 9. Attempt Questions
    print("\nStep 9: Attempting Questions...")
    try:
        for i in range(10): 
            nq_resp = requests.get(f"{BASE_URL}/interview/next-question/{interview_id}", headers=cand_headers, timeout=TIMEOUT)
            full_data = log_response(nq_resp, f"Next Question {i+1}")
            if not full_data or not full_data.get("data"): break
            
            q_info = full_data["data"]
            if q_info.get("status") == "finished":
                print("All questions reached.")
                break
                
            q_id = q_info["question_id"]
            resp_type = q_info.get("response_type")
            
            if resp_type == "code":
                real_cq_id = q_info.get("coding_question_id") or q_info.get("coding_question", {}).get("id") if isinstance(q_info.get("coding_question"), dict) else None
                if not real_cq_id:
                    real_cq_id = q_id  # fallback to proxy id
                print(f"Submitting code for coding_question_id {real_cq_id}")
                code_answer = """def inorder_traversal(root):
    res = []
    def helper(node):
        if node:
            helper(node.left)
            res.append(node.val)
            helper(node.right)
    helper(root)
    return res"""
                requests.post(
                    f"{BASE_URL}/interview/submit-answer-code",
                    headers=cand_headers,
                    data={
                        "interview_id": interview_id,
                        "coding_question_id": real_cq_id,
                        "answer_code": code_answer
                    },
                    timeout=TIMEOUT
                )
            else:
                print(f"Submitting text for question_id {q_id}")
                text_ans = "A decorator in Python is a function that takes another function and extends its behavior without explicitly modifying it. They are commonly used for logging, access control, and instrumentation, using the @decorator_name syntax above function definitions."
                if "FastAPI" in q_info.get("text", ""):
                    text_ans = "FastAPI handles asynchronous requests using Python's async and await keywords. It is built on Starlette and uses an ASGI server like Uvicorn to handle non-blocking I/O operations efficiently, allowing many concurrent connections."
                
                requests.post(
                    f"{BASE_URL}/interview/submit-answer-text",
                    headers=cand_headers,
                    data={
                        "interview_id": interview_id,
                        "question_id": q_id,
                        "answer_text": text_ans
                    },
                    timeout=TIMEOUT
                )
            print(f"Question {i+1} submitted.")
    except Exception as e:
        print(f"Attempt Questions Error: {e}")

    # 10. Finish Interview
    print("\nStep 10: Finishing Interview...")
    requests.post(f"{BASE_URL}/interview/finish/{interview_id}", headers=cand_headers, timeout=TIMEOUT)

    # 11. View Results (Admin)
    print("\nStep 11: Viewing Results as Admin...")
    result_resp = requests.get(f"{BASE_URL}/admin/results/{interview_id}", headers=headers, timeout=TIMEOUT)
    log_response(result_resp, "Final Result")

    print(f"\nTotal Time: {time.time() - total_start:.2f}s")

if __name__ == "__main__":
    run_test()
