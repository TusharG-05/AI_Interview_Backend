import requests
import json
import time
from datetime import datetime, timezone
import os

# --- Configuration ---
SPACE_URL = "http://localhost:8000"
BASE_URL = f"{SPACE_URL}/api"
ADMIN_EMAIL = "simadmin@test.com"
ADMIN_PASS = "sim123"

def run_simulation(phase_name="Modal (Local)"):
    print(f"🚀 Starting Phase: {phase_name}...")
    
    # 1. Login Admin
    print("\n[1] Logging in as Admin...")
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    if admin_login.status_code != 200:
        print(f"❌ Admin login failed: {admin_login.text}")
        return
    
    admin_data = admin_login.json()["data"]
    admin_token = admin_data["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 2. Get a Candidate ID (Any user with CANDIDATE role)
    # To be safe, try to create one or find one.
    print("[2] Finding/Creating a valid Candidate ID...")
    # List candidates
    c_list = requests.get(f"{BASE_URL}/admin/candidates", headers=headers)
    candidate_id = None
    if c_list.status_code == 200:
        # Some versions return a list, some a dict with 'data'
        data = c_list.json().get("data", [])
        if isinstance(data, list) and len(data) > 0:
            candidate_id = data[0]["id"]
            print(f"   Found existing candidate ID: {candidate_id}")
    
    if not candidate_id:
        # Create one
        create_res = requests.post(
            f"{BASE_URL}/admin/users",
            headers=headers,
            json={
                "email": f"sim_can_{int(time.time())}@test.com",
                "password": "password123",
                "full_name": "Sim Candidate",
                "role": "CANDIDATE"
            }
        )
        if create_res.status_code in [200, 201]:
            candidate_id = create_res.json()["data"]["id"]
            print(f"   Created new candidate ID: {candidate_id}")
        else:
            print(f"❌ Could not obtain candidate ID: {create_res.text}")
            return

    # 3. Generate Paper (20 Questions)
    print(f"[3] Generating 20-question Paper (Groq)...")
    start_gen = time.time()
    gen_res = requests.post(
        f"{BASE_URL}/admin/generate-paper",
        headers=headers,
        json={
            "ai_prompt": "Mixed Python basics and FastAPI advanced features.",
            "num_questions": 20,
            "years_of_experience": 2,
            "team_id": 1,
            "paper_name": f"Paper_{int(time.time())}"
        }
    )
    gen_duration = time.time() - start_gen
    
    if gen_res.status_code != 201:
        print(f"❌ Paper generation failed: {gen_res.text}")
        return
    
    paper_data = gen_res.json()["data"]
    paper_id = paper_data["id"]
    questions = paper_data["questions"]
    print(f"✅ Generated {len(questions)} questions in {gen_duration:.2f}s.")

    # 4. Schedule Interview
    print("[4] Scheduling Interview Session...")
    schedule_res = requests.post(
        f"{BASE_URL}/admin/interviews/schedule",
        headers=headers,
        json={
            "candidate_id": candidate_id,
            "paper_id": paper_id,
            "team_id": 1,
            "interview_round": "ROUND_1",
            "schedule_time": datetime.now(timezone.utc).isoformat()
        }
    )
    if schedule_res.status_code not in [200, 201]:
        print(f"❌ Scheduling failed: {schedule_res.text}")
        return
    
    interview_id = schedule_res.json()["data"]["interview"]["id"]
    print(f"✅ Interview Scheduled (ID: {interview_id})")
    
    # 5. Conduct Interview using Admin Token
    print(f"[5] Answering {len(questions)} Questions (Admin proxying for Candidate)...")
    eval_timings = []
    
    answers = [
        "A list is mutable while a tuple is immutable in Python.", # Q1
        "GIL stands for Global Interpreter Lock, it limits execution to one thread.", # Q2
        "List comprehensions provide a shorter syntax for creating lists based on existing lists.", # Q3
        "Pydantic is for data validation using Python type annotations.", # Q4
        "FastAPI is very fast compared to Flask or Django.", # Q5
        "Uvicorn is an ASGI implementation.", # Q6
        "Async/await allows writing asynchronous code that looks like synchronous code.", # Q7
        "Decorators allow us to wrap another function and extend its behavior.", # Q8
        "The 'with' statement is used for resource management.", # Q9
        "I don't know much about this topic.", # Q10
        "FastAPI's BackgroundTasks are for execution after the response.", # Q11
        "Python is interpreted.", # Q12
        "Variables are dynamically typed.", # Q13
        "Inheritance allows a class to inherit from parent.", # Q14
        "Polymorphism is many forms.", # Q15
        "Encapsulation restricts access to data.", # Q16
        "Abstraction hides internal details.", # Q17
        "FastAPI dependency injection is very powerful.", # Q18
        "Middleware sits between client and handler.", # Q19
        "Starlette provides the low-level web tools for FastAPI." # Q20
    ]
    
    for i, q in enumerate(questions):
        print(f"   Answering Q{i+1}/20...")
        q_id = q["id"]
        ans_text = answers[i] if i < len(answers) else "Simulation answer."
        
        start_eval = time.time()
        submit_res = requests.post(
            f"{BASE_URL}/interview/submit-answer-text",
            headers=headers,
            data={
                "interview_id": interview_id,
                "question_id": q_id,
                "answer_text": ans_text
            }
        )
        eval_duration = time.time() - start_eval
        
        if submit_res.status_code == 200:
            eval_data = submit_res.json()["data"]
            eval_timings.append({
                "question": q["question_text"],
                "score": eval_data["score"],
                "duration": eval_duration
            })
        else:
            print(f"   ⚠️ Submission failed: {submit_res.text}")

    # 6. Final Report
    avg_eval = sum(t["duration"] for t in eval_timings) / len(eval_timings) if eval_timings else 0
    
    report_md = f"""# Mock Interview Simulation Report: {phase_name}
- **Phase:** {phase_name}
- **Timestamp:** {datetime.now(timezone.utc).isoformat()}
- **Questions Generated:** {len(questions)}
- **Generation Duration:** {gen_duration:.2f}s
- **Average Eval Latency:** {avg_eval:.4f}s

| # | Question Snippet | Score | Latency (s) |
|---|---|---|---|
"""
    for i, t in enumerate(eval_timings):
        report_md += f"| {i+1} | {t['question'][:50]}... | {t['score']} | {t['duration']:.4f} |\n"
        
    filename = f"simulation_report_{phase_name.replace(' ', '_').lower()}.md"
    with open(filename, "w") as f:
        f.write(report_md)
    
    print(f"\n✅ Simulation Complete. Report: {filename}")
    return report_md

if __name__ == "__main__":
    run_simulation()
