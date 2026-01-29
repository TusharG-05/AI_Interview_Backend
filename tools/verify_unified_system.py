import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_URL = "https://localhost:8000"

def check(method, path, data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET": r = requests.get(url, verify=False)
        else: r = requests.post(url, json=data, verify=False)
        print(f"[{method}] {path: <25} | Status: {r.status_code}")
        return r
    except Exception as e:
        print(f"[{method}] {path: <25} | ERROR: {e}")
        return None

print("--- System Integrity Check ---")
check("GET", "/status/")
check("GET", "/admin/questions") # Should 401 without token, but 404 means route is gone
check("GET", "/interview/general-questions")
check("GET", "/video/video_feed")
check("GET", "/")

# Mock Login to test auth routes if needed, but 401 proves route exists
print("\n--- Integrity Check Finished ---")
