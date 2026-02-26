import sys
from passlib.context import CryptContext

# Replicate the exact hashing scheme from the backend
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash_password.py <password_to_hash>")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = get_password_hash(password)
    
    print(f"\nOriginal Password: {password}")
    print(f"Hashed Password (pbkdf2_sha256):")
    print("-" * 50)
    print(hashed)
    print("-" * 50)
    print("\nYou can use this hash directly in your database seed scripts.")
