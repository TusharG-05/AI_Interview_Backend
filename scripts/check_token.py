import sys
import os
from dotenv import load_dotenv

# Ensure we can import from the app directory
sys.path.append(os.getcwd())

load_dotenv()

from app.auth.security import create_access_token
from jose import jwt, JWTError

def test_token_logic():
    print("Testing Token Generation...")
    
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    print(f"Generated Token: {token[:20]}...")
    
    secret = os.getenv("SECRET_KEY")
    if not secret:
        print("Error: SECRET_KEY not found in environment")
        return
        
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
