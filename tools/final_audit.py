import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_URL = "https://localhost:8000"

def test(method, path, data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET": r = requests.get(url, verify=False, timeout=10)
        else: r = requests.post(url, json=data, verify=False, timeout=10)
        print(f"[{method}] {path: <30} | Status: {r.status_code}")
        if r.status_code == 200 and "status" in path:
            print(f"   Payload: {r.text[:100]}...")
        return r
    except Exception as e:
        print(f"[{method}] {path: <30} | ERROR: {str(e)}")
        return None

print("--- FINAL SYSTEM AUDIT ---")
test("GET", "/status/")
test("GET", "/")
test("GET", "/interview/general-questions")
test("GET", "/admin/history") # Expected 401
test("GET", "/video/video_feed") # This is a stream, might timeout or 200
print("--- AUDIT COMPLETE ---")
