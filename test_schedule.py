import asyncio
from httpx import AsyncClient, ASGITransport
from app.server import app

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        resp = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        token = resp.json().get("data", {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a paper ID
        papers_resp = await client.get("/api/admin/papers?limit=1", headers=headers)
        papers = papers_resp.json().get("data", {}).get("items", [])
        if not papers:
            print("No papers found! Cannot schedule.")
            return
        paper_id = papers[0].get("id")
        
        # Schedule Interview
        cand_id = 281
        print(f"Scheduling HR_ROUND interview for candidate ID {cand_id}...")
        schedule_data = {
            "candidate_id": cand_id,
            "schedule_time": "2026-06-20T10:00:00Z",
            "duration_minutes": 30,
            "interview_round": "HR_ROUND",
            "paper_id": paper_id
        }
        sched_resp = await client.post("/api/admin/interviews/schedule", json=schedule_data, headers=headers)
        print("Schedule Response Code:", sched_resp.status_code)
        print("Response Body:", sched_resp.text)

if __name__ == "__main__":
    asyncio.run(main())
