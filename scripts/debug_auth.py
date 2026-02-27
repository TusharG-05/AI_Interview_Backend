from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User
from app.auth.security import verify_password, get_password_hash

def debug_auth():
    with Session(engine) as session:
        u = session.exec(select(User).where(User.email == "admin@test.com")).first()
        if not u:
            print("User not found!")
            return
        
        print(f"User: {u.email}")
        print(f"Hashed in DB: {u.password_hash}")
        
        # Test direct verification
        res = verify_password("admin123", u.password_hash)
        print(f"Verify 'admin123': {res}")
        
        # Test new hash
        new_hash = get_password_hash("admin123")
        print(f"New hash of 'admin123': {new_hash}")
        print(f"Verify new hash: {verify_password('admin123', new_hash)}")

if __name__ == "__main__":
    debug_auth()
