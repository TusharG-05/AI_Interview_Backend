import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from config.database import engine
from models.db_models import User, UserRole
from auth.security import get_password_hash

def create_super_admin():
    with Session(engine) as session:
        statement = select(User).where(User.email == "admin@test.com")
        existing_user = session.exec(statement).first()
        
        if not existing_user:
            print("Creating default super admin...")
            super_admin = User(
                email="admin@test.com",
                full_name="Super Admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN
            )
            session.add(super_admin)
            session.commit()
            print("Super admin created successfully.")
        else:
            print("Super admin already exists.")

if __name__ == "__main__":
    create_super_admin()
