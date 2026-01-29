import sys
import os
sys.path.append(os.getcwd())

from auth.security import create_access_token, verify_password, get_password_hash
from jose import jwt, JWTError
from datetime import timedelta

def test_token_logic():
    print("Testing Token Generation...")
    
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    print(f"Generated Token: {token[:20]}...")
    
    secret = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    algorithm = "HS256"
    
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        email = payload.get("sub")
        print(f"Decoded Email: {email}")
        if email == "test@example.com":
            print("Token verification SUCCESS")
        else:
            print("Token verification FAILED: Email mismatch")
    except JWTError as e:
        print(f"Token verification FAILED: {e}")

if __name__ == "__main__":
    test_token_logic()
