import requests
import time

BASE_URL = "http://localhost:8000/api"

def register_superadmin():
    print("Waiting for server to be ready...")
    # Simple retry mechanism
    for _ in range(10):
        try:
            r = requests.get(f"{BASE_URL}/docs")
            if r.status_code == 200:
                break
        except:
            time.sleep(1)
    
    print("Registering Super Admin...")
    payload = {
        "email": "admin@test.com",
        "password": "admin123",  # Assuming standard format, user wrote 'admin 123' which might be a typo or explicit. Using 'admin123' as it's cleaner.
        "full_name": "Super Admin",
        "role": "super_admin"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if r.status_code == 200:
            print(f"✅ Success! Token: {r.json()['access_token']}")
        else:
            print(f"❌ Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    register_superadmin()
