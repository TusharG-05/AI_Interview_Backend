
import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from sqlmodel import Session, select
except ImportError:
    # Fallback or ensuring package is installed
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlmodel"])
    from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def create_custom_admin():
    print("Connecting to DB...")
    with Session(engine) as session:
        email = "admin@test.com"
        password = "admin123"
        
        user = session.exec(select(User).where(User.email == email)).first()
        
        if user:
            print(f"User {email} found. Updating password...")
            user.password_hash = get_password_hash(password)
            user.role = UserRole.ADMIN 
            session.add(user)
            session.commit()
            print("Admin updated.")
        else:
            print(f"User {email} not found. Creating...")
            user = User(
                email=email,
                full_name="Test Admin",
                password_hash=get_password_hash(password),
                role=UserRole.ADMIN
            )
            session.add(user)
            session.commit()
            print(f"Admin {email} created successfully.")

if __name__ == "__main__":
    create_custom_admin()
