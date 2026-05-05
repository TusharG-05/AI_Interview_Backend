import asyncio
import websockets
import json

async def test_admin_ws():
    """Test admin WebSocket connection"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3ODA2NzM5N30.d3ZiMDgMB4hf3ttm2j5cnLbsBRLlfLTXYLIDfgo-0CE"
    url = f"ws://127.0.0.1:8000/api/dashboard/ws?token={token}"
    
    print(f"🔗 Connecting to: {url}")
    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connected successfully!")
            print("   Admin dashboard is now listening for events...")
            
            # Keep connection alive for 5 seconds
            for i in range(5):
                await asyncio.sleep(1)
                print(f"   ⏱️  Still connected ({i+1}s)...")
            
            print("✅ Test passed! Connection remained open.")
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for message")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

asyncio.run(test_admin_ws())
