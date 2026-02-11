import sys
import os
import argparse
from dotenv import load_dotenv

# Add parent directory to path so we can import from app
sys.path.append(os.getcwd())
load_dotenv()

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def create_super_admin(email, password, full_name):
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        existing_user = session.exec(statement).first()
        
        if not existing_user:
            print(f"Creating super admin: {email}...")
            super_admin = User(
                email=email,
                full_name=full_name,
                password_hash=get_password_hash(password),
                role=UserRole.SUPER_ADMIN
            )
            session.add(super_admin)
            session.commit()
            print("Super admin created successfully.")
        else:
            print(f"User with email {email} already exists.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a super admin user.")
    parser.add_argument("--email", default="admin@test.com", help="Admin email")
    parser.add_argument("--password", default="admin123", help="Admin password")
    parser.add_argument("--name", default="Super Admin", help="Admin full name")
    
    args = parser.parse_args()
    create_super_admin(args.email, args.password, args.name)
