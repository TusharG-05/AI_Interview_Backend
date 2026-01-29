import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8000"

def test_endpoint(method, path, data=None, params=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, verify=False, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, verify=False, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, verify=False, params=params)
        elif method == "DELETE":
            response = requests.delete(url, verify=False, params=params)
        
        print(f"[{method}] {path: <40} | Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"[{method}] {path: <40} | ERROR: {str(e)}")
        return None

endpoints = [
    ("GET", "/"),
    ("GET", "/login"),
    ("GET", "/register"),
    ("GET", "/admin-panel"),
    ("GET", "/webcam-test"),
    ("GET", "/status"),
    ("GET", "/interview/general-questions"),
    ("POST", "/interview/evaluate", {"candidate_text": "test", "reference_text": "test"}),
    ("POST", "/interview/evaluate-answer", {"question": "test", "answer": "test"}, {"session_id": 1}),
    ("GET", "/admin/history"),
    ("GET", "/admin/rooms"),
    ("GET", "/admin/users"),
]

print("--- Starting Endpoints Audit ---\n")
for m, p, *rest in endpoints:
    data = rest[0] if len(rest) > 0 else None
    params = rest[1] if len(rest) > 1 else None
    test_endpoint(m, p, data, params)

print("\n--- Audit Finished ---")
