"""
Quick test script for new API response format
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Login Endpoint with New Response Format")
print("=" * 60)

# Test login
login_data = {
    "email": "admin@example.com",
    "password": "Admin123!"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if "status_code" in data and "data" in data and "message" in data:
            print("\n[OK] New response format is working!")
            print(f"   - status_code: {data['status_code']}")
            print(f"   - message: {data['message']}")
            print(f"   - data keys: {list(data['data'].keys())}")
        else:
            print("\n[ERROR] Response doesn't match expected format")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")

print("\n" + "=" * 60)
