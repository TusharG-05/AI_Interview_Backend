"""
Quick test script to verify /auth/me fix
"""
import requests

BASE_URL = "http://localhost:8000/api"

# Login to get token
print("1. Testing login...")
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@test.com",
    "password": "admin123"
})

if response.status_code == 200:
    data = response.json()
    token = data["data"]["access_token"]
    print(f"   [OK] Login successful, token: {token[:20]}...")
    
    # Test /auth/me
    print("\n2. Testing GET /auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Success!")
        print(f"   User: {data['data']}")
        print(f"\n   ✅ BUG FIXED! /auth/me now works correctly")
    else:
        print(f"   [FAIL] Still broken: {response.text}")
else:
    print(f"   [FAIL] Login failed: {response.status_code}")
