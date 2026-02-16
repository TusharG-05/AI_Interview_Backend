import asyncio
import websockets
import json

async def test_admin_websocket():
    uri = "ws://localhost:8000/api/admin/dashboard/ws"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Listening for events... (Press Ctrl+C to stop)")
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                print("\n📩 RECEIVED MSG:")
                if data.get("type") == "violation":
                    print(f"   ⚠️ VIOLATION: {data['data']['type']}")
                    print(f"      Details: {data['data']['details']}")
                    print(f"      Session: {data['interview_id']}")
                elif data.get("type") == "status_change":
                    print(f"   🔄 STATUS CHANGE: {data['data']['status']}")
                    print(f"      Session: {data['interview_id']}")
                else:
                    print(f"   ℹ️ OTHER: {data}")
                    
    except ConnectionRefusedError:
        print("❌ Connection Failed. Is the server running on localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_admin_websocket())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
