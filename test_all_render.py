import asyncio
import httpx

async def test_endpoint(client, method, url, headers=None, json=None, expected_status=200):
    try:
        resp = await client.request(method, url, headers=headers, json=json)
        if resp.status_code == expected_status:
            print(f"✅ [PASS] {method} {url}")
            return True, resp
        else:
            print(f"❌ [FAIL] {method} {url} - Expected {expected_status}, got {resp.status_code}")
            try:
                print(f"   Response: {resp.json()}")
            except:
                print(f"   Response: {resp.text}")
            return False, resp
    except Exception as e:
        print(f"❌ [ERROR] {method} {url} - {str(e)}")
        return False, None

async def main():
    BASE_URL = "https://ai-interview-backend-ghqt.onrender.com"
    print(f"Starting Comprehensive API Test on {BASE_URL}...\n")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Auth & Login
        success, resp = await test_endpoint(client, "POST", "/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        if not success:
            print("Aborting remaining tests due to login failure.")
            return
            
        token = resp.json().get("data", {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Endpoints to test (GET)
        endpoints = [
            "/api/auth/me",
            "/api/admin/candidates?skip=0&limit=10",
            "/api/admin/papers?skip=0&limit=10",
            "/api/admin/coding_papers?skip=0&limit=10",
            "/api/admin/interviews?skip=0&limit=10",
            "/api/admin/questions?skip=0&limit=10",
            "/api/teams/?skip=0&limit=10",
            "/api/settings/",  # Test settings endpoint if exists
        ]
        
        for ep in endpoints:
            await test_endpoint(client, "GET", ep, headers=headers)
            
        # 3. Schedule Interview (POST)
        print("\n--- Testing Action APIs ---")
        
        # We need a candidate ID and paper ID for schedule testing
        cand_resp = await client.get("/api/admin/candidates?limit=1", headers=headers)
        paper_resp = await client.get("/api/admin/papers?limit=1", headers=headers)
        
        if cand_resp.status_code == 200 and paper_resp.status_code == 200:
            cands = cand_resp.json().get("data", {}).get("items", [])
            papers = paper_resp.json().get("data", {}).get("items", [])
            
            if cands and papers:
                cand_id = cands[0]["id"]
                paper_id = papers[0]["id"]
                
                schedule_data = {
                    "candidate_id": cand_id,
                    "schedule_time": "2026-06-25T10:00:00Z",
                    "duration_minutes": 30,
                    "interview_round": "HR_ROUND",
                    "paper_id": paper_id
                }
                await test_endpoint(client, "POST", "/api/admin/interviews/schedule", headers=headers, json=schedule_data, expected_status=201)

if __name__ == "__main__":
    asyncio.run(main())
