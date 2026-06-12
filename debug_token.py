import requests
from jose import jwt

BASE_URL = "http://localhost:8000/api"
res = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@test.com", "password": "admin123"})
token = res.json()["data"]["access_token"]
print("Token:", token)

# Decode token
from app.auth.security import SECRET_KEY, ALGORITHM
print("SECRET_KEY:", SECRET_KEY)
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("Decoded:", payload)
except Exception as e:
    print("Decode failed:", e)

res2 = requests.get(f"{BASE_URL}/admin/candidates", headers={"Authorization": f"Bearer {token}"})
print("Auth Test:", res2.status_code, res2.text)
