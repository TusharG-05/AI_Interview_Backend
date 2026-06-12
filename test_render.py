import asyncio
import httpx

async def main():
    BASE_URL = "https://ai-interview-backend-ghqt.onrender.com"
    print(f"Testing on {BASE_URL}")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Test Login
        print("\n--- 1. Testing Login ---")
        resp = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        if resp.status_code != 200:
            print("Login failed:", resp.status_code, resp.text)
            return
        
        token = resp.json().get("data", {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # 2. Test Fetching Candidates
        print("\n--- 2. Testing Fetch Candidates ---")
        cand_resp = await client.get("/api/admin/candidates?skip=0&limit=20", headers=headers)
        if cand_resp.status_code != 200:
            print("Fetch candidates failed:", cand_resp.status_code, cand_resp.text)
            print("NOTE: This means the bug fix has not been deployed to Render yet!")
        else:
            candidates = cand_resp.json().get("data", {}).get("items", [])
            print(f"Fetch candidates successful. Found {len(candidates)} candidates.")
        
        # 3. Test Fetching Papers
        print("\n--- 3. Testing Fetch Papers ---")
        papers_resp = await client.get("/api/admin/papers?limit=1", headers=headers)
        if papers_resp.status_code != 200:
            print("Fetch papers failed:", papers_resp.text)
            return
        papers = papers_resp.json().get("data", {}).get("items", [])
        if not papers:
            print("No papers found. Cannot test scheduling.")
            return
        paper_id = papers[0].get("id")
        
        # 4. Test Scheduling HR_ROUND
        print("\n--- 4. Testing HR_ROUND Scheduling ---")
        cand_id = 281
        schedule_data = {
            "candidate_id": cand_id,
            "schedule_time": "2026-06-25T10:00:00Z",
            "duration_minutes": 30,
            "interview_round": "HR_ROUND",
            "paper_id": paper_id
        }
        sched_resp = await client.post("/api/admin/interviews/schedule", json=schedule_data, headers=headers)
        if sched_resp.status_code == 201:
            print("HR_ROUND Scheduling successful!")
        else:
            print("Scheduling failed:", sched_resp.status_code, sched_resp.text)
            print("NOTE: If this is 500 InvalidTextRepresentation, the Alembic migration hasn't been deployed yet!")

if __name__ == "__main__":
    asyncio.run(main())
