import requests
import json

BASE_URL = "https://ichigo253-ai-interview-backend.hf.space/api"

def debug_cloud():
    # Attempt to get next-question for a known ID or standalone TTS
    print("Testing Standalone TTS...")
    r = requests.get(f"{BASE_URL}/interview/tts", params={"text": "Debug message"})
    print(f"TTS Status: {r.status_code}")
    if r.status_code != 200:
        print(f"TTS Error Body: {r.text}")

    print("\nTesting Next Question (ID 10)...")
    r = requests.get(f"{BASE_URL}/interview/next-question/10")
    print(f"Next-Q Status: {r.status_code}")
    print(f"Next-Q Body: {r.text}")

    print("\nTesting Health Status...")
    r = requests.get(f"{BASE_URL}/status/")
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")

if __name__ == "__main__":
    debug_cloud()
