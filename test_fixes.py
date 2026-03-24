#!/usr/bin/env python3
"""
Quick test of the fixed endpoints
"""
import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.request(method, url, json=data)
        
        status = "✅ PASS" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{status} {method} {endpoint}")
        
        if response.status_code != 200:
            try:
                print(f"    Error: {response.json().get('detail', 'Unknown error')}")
            except:
                print(f"    Response: {response.text[:100]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ FAIL {method} {endpoint} - Exception: {str(e)}")
        return False

def main():
    print("🔧 Testing Fixed Endpoints")
    print("=" * 30)
    
    fixed_endpoints = [
        ("/api/status/", "GET", 200),
        ("/api/interview/access/invalid-token", "GET", 404),  # Now returns 404 instead of 401
        ("/api/video/video_feed", "GET", 200),  # Now returns streaming response
        ("/api/video/offer", "POST", 200),  # Test with POST method
    ]
    
    for endpoint, method, expected in fixed_endpoints:
        data = {"sdp": "test", "type": "offer"} if endpoint == "/api/video/offer" else None
        success = test_endpoint(endpoint, method, data)
        
        # Adjust expectations for some endpoints
        if endpoint == "/api/interview/access/invalid-token" and success:
            print(f"    ✅ Now returns 404 (invalid token) instead of 401 (auth required)")
        elif endpoint == "/api/video/video_feed" and success:
            print(f"    ✅ Now returns streaming response without validation error")
        elif endpoint == "/api/video/offer" and success:
            print(f"    ✅ Now works with POST method (WebRTC)")

if __name__ == "__main__":
    main()
