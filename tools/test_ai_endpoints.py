import requests
import os

BASE_URL = "https://localhost:8000/interview"

def test_evaluate():
    print("\n--- Testing Standalone Evaluate ---")
    payload = {
        "candidate_text": "Python is a programming language.",
        "reference_text": "Python is a widely used high-level programming language."
    }
    try:
        response = requests.post(f"{BASE_URL}/evaluate", json=payload, verify=False)
        response.raise_for_status()
        result = response.json()
        print(f"Result: {result}")
        if "score" in result and result["score"] > 0.5:
            print("✅ NLP Evaluation test passed.")
        else:
            print("❌ NLP Evaluation test failed (Unexpected score).")
    except Exception as e:
        print(f"❌ NLP Evaluation test failed: {e}")

def test_tts():
    print("\n--- Testing Standalone TTS ---")
    payload = {
        "text": "This is a standalone test of the AI speech system."
    }
    try:
        response = requests.post(f"{BASE_URL}/tts", json=payload, verify=False)
        response.raise_for_status()
        if response.headers.get("Content-Type") == "audio/mpeg":
            content_len = len(response.content)
            print(f"Received {content_len} bytes of audio.")
            if content_len > 1000:
                print("✅ TTS test passed.")
            else:
                print("❌ TTS test failed (Audio too short).")
        else:
            print(f"❌ TTS test failed (Wrong Content-Type: {response.headers.get('Content-Type')})")
    except Exception as e:
        print(f"❌ TTS test failed: {e}")

if __name__ == "__main__":
    print("Ensure the server is running at http://localhost:8000 before starting tests.")
    test_evaluate()
    test_tts()
