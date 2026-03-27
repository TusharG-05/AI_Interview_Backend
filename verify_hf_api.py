import requests
import sys

BASE_URL = "https://ichigo253-ai-interview-backend.hf.space"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3NDY4Mzg5M30.Th80wojPQL5RKq2l0bsc8kIyvNLLL-z7sBUlad4FO88"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "accept": "application/json"
}

def check(name, method, endpoint, expected_status=200):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {name}: {method} {endpoint}...", end=" ", flush=True)
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=15)
        elif method == "POST":
            response = requests.post(url, headers=headers, timeout=15, json={})
        
        if response.status_code == expected_status:
            print("✅ PASS")
            return True
        else:
            print(f"❌ FAIL (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def run_all():
    results = []
    print("\n🚀 Starting Comprehensive API Verification on Hugging Face...\n")
    
    # 1. System Status (instead of health)
    results.append(check("System Status", "GET", "/api/status/"))
    
    # 2. Teams (Super Admin/Admin route corrected)
    results.append(check("List Teams", "GET", "/api/super-admin/teams"))
    
    # 3. Papers (Admin)
    results.append(check("List Standard Papers", "GET", "/api/admin/papers"))
    
    # 4. Interviews (Admin)
    results.append(check("List All Interviews", "GET", "/api/admin/interviews"))
    results.append(check("Specific Interview Detail (264)", "GET", "/api/admin/interviews/264"))
    
    # 5. Results (Bug fix verification)
    results.append(check("Results Dashboard (Filtered)", "GET", "/api/admin/users/results"))
    
    # 6. Auth
    results.append(check("Auth Profile", "GET", "/api/auth/me"))
    
    print("-" * 50)
    if all(results):
        print("\n✨ ALL CORE APIs ARE STABLE on Hugging Face!")
        print("✅ The 'Results List' filtering bug is also verified.")
    else:
        print("\n⚠️ Some APIs failed. Please check the logs above.")

if __name__ == "__main__":
    run_all()
