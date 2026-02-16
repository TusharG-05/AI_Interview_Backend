import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def ensure_admin():
    print("Connecting to DB...")
    with Session(engine) as session:
        email = "admin_sim@example.com"
        password = "password123"
        
        user = session.exec(select(User).where(User.email == email)).first()
        
        if user:
            print(f"User {email} found. Updating password...")
            user.password_hash = get_password_hash(password)
            user.role = UserRole.ADMIN # Ensure role
            session.add(user)
            session.commit()
            print("Password updated.")
        else:
            print(f"User {email} not found. Creating...")
            user = User(
                email=email,
                full_name="Sim Admin",
                password_hash=get_password_hash(password),
                role=UserRole.ADMIN
            )
            session.add(user)
            session.commit()
            print(f"User {email} created.")

if __name__ == "__main__":
    ensure_admin()
