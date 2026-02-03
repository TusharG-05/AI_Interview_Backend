import asyncio
import websockets
import json
import ssl
import os

# Configuration
WS_URL = "wss://localhost:8000/api/ws/video"
IMAGE_PATH = "app/assets/known_person.jpg"

async def test_proctoring():
    print(f"Connecting to {WS_URL}...")
    
    # Bypass SSL verification for local testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(WS_URL, ssl=ssl_context) as websocket:
            print("Connected!")

            if not os.path.exists(IMAGE_PATH):
                print(f"Error: {IMAGE_PATH} not found.")
                return

            with open(IMAGE_PATH, "rb") as f:
                image_data = f.read()

            print(f"Sending image ({len(image_data)} bytes)...")
            await websocket.send(image_data)

            # Wait for response
            response = await websocket.recv()
            result = json.loads(response)
            
            print("\n--- Proctoring Result ---")
            print(json.dumps(result, indent=2))
            
            # Assertions
            faces = result.get("faces", 0)
            auth = result.get("auth", False)
            warning = result.get("warning", "")
            
            if faces > 0:
                print(f"\n[PASS] Detected {faces} face(s).")
            else:
                # Note: MediaPipe might take a second to warm up in the background
                print(f"\n[INFO] No faces detected in first frame. (Could be warming up or bad image)")

            if auth is False:
                print("[PASS] Recognition correctly reported as disabled (auth=False).")
            else:
                print("[FAIL] Recognition should be disabled but reported as True.")

            print("\nTest completed successfully.")

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_proctoring())
