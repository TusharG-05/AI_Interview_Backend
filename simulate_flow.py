import requests
import json
import webbrowser

BASE_URL = "https://lasandra-disputable-nonconvertibly.ngrok-free.dev/api"
# Or use localhost if preferred:
# BASE_URL = "http://localhost:8000/api"

def print_step(title):
    print(f"\n{'='*50}")
    print(f"🔹 STEP: {title}")
    print(f"{'='*50}")

def post(path, data, headers=None):
    url = f"{BASE_URL}{path}"
    print(f"Sending POST to {url}...")
    try:
        resp = requests.post(url, json=data, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            content = resp.json()
            print(f"Response: {json.dumps(content, indent=2)}")
            return content
        except:
            print(f"Raw: {resp.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_simulation():
    # 1. Login as Super Admin
    print_step("Login as Super Admin")
    token = None
    resp = post("/auth/login", {"email": "admin@test.com", "password": "admin123"})
    if resp and "data" in resp:
        token = resp["data"]["access_token"]
        print("✅ Login Successful! Token acquired.")
    else:
        print("❌ Login Failed. Exiting.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a Question Paper
    print_step("Create Question Paper")
    paper_id = None
    paper_data = {
        "name": "Python Mastery",
        "description": "Advanced Python concepts for senior developers."
    }
    resp = post("/admin/papers", paper_data, headers=headers)
    if resp and "data" in resp:
        paper_id = resp["data"]["id"]
        print(f"✅ Paper Created! ID: {paper_id}")
    
    if not paper_id: return

    # 3. Add Questions
    print_step("Add Questions to Paper")
    q1 = {
        "content": "Explain the Global Interpreter Lock (GIL).",
        "topic": "Concurrency",
        "difficulty": "Hard"
    }
    post(f"/admin/papers/{paper_id}/questions", q1, headers=headers)
    
    q2 = {
        "content": "What are Python decorators?",
        "topic": "Functions",
        "difficulty": "Medium"
    }
    post(f"/admin/papers/{paper_id}/questions", q2, headers=headers)
    print("✅ Questions Added!")

    # 4. Schedule Interview
    print_step("Schedule Interview for Candidate")
    
    # 4a. Get Candidate ID (Simulating frontend selection)
    print("Fetching candidate list to find 'Aarav'...")
    candidates = requests.get(f"{BASE_URL}/admin/candidates", headers=headers).json()["data"]
    candidate = next((c for c in candidates if c["email"] == "aarav@example.com"), None)
    
    if not candidate:
        print("⚠️ Candidate 'Aarav' not found. Creating him now...")
        new_user = {
            "email": "aarav@example.com",
            "full_name": "Aarav Sharma",
            "password": "password123",
            "role": "candidate"
        }
        resp = post("/admin/users", new_user, headers=headers)
        if resp and "data" in resp:
            candidate = resp["data"]
            print(f"✅ Candidate Created: {candidate['full_name']} (ID: {candidate['id']})")
        else:
            print("❌ Failed to create candidate. Exiting.")
            return

    print(f"✅ Found Candidate: {candidate['full_name']} (ID: {candidate['id']})")

    schedule_data = {
        "candidate_id": candidate["id"],
        "paper_id": paper_id,
        "schedule_time": "2026-02-12T10:00:00", 
        "duration_minutes": 60
    }
    resp = post("/admin/interviews/schedule", schedule_data, headers=headers)
    
    if resp and "data" in resp:
        meeting_link = resp["data"]["meeting_link"]
        print(f"\n🎉 INTERVIEW SCHEDULED SUCCESSFULLY!")
        print(f"🔗 Meeting Link: {meeting_link}")
        # webbrowser.open(meeting_link) # Optional: Open in browser
    else:
        print("❌ Scheduling Failed.")

if __name__ == "__main__":
    run_simulation()
