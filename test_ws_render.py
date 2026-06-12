import asyncio
import websockets
import httpx

async def test_ws():
    BASE_URL = "https://ai-interview-backend-ghqt.onrender.com"
    
    print("1. Logging in to get token...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        if resp.status_code != 200:
            print("Login failed:", resp.status_code)
            return
        token = resp.json().get("data", {}).get("access_token")
        
        # Get an interview ID
        interviews_resp = await client.get("/api/admin/interviews?limit=1", headers={"Authorization": f"Bearer {token}"})
        interviews = interviews_resp.json().get("data", {}).get("items", [])
        if not interviews:
            print("No interviews found to test WS.")
            return
        interview_id = interviews[0]["id"]
        
    WS_URL = f"wss://ai-interview-backend-ghqt.onrender.com/ws/api/dashboard/{interview_id}?token={token}"
    print(f"2. Connecting to WebSocket at /ws/api/dashboard/{interview_id}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ WebSocket Connection Successful!")
            # Send a ping or simple message if needed
            # We just need to check connection success
    except Exception as e:
        print(f"WebSocket Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
