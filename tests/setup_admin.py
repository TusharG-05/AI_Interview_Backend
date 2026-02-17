import sys
import os
from threading import Timer

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def setup_test_users():
    with Session(engine) as session:
        # 1. Ensure Admin Exists
        admin_email = "admin@test.com"
        admin = session.exec(select(User).where(User.email == admin_email)).first()
        
        if not admin:
            print(f"Creating admin user: {admin_email}")
            admin = User(
                email=admin_email,
                full_name="Test Admin",
                password_hash=get_password_hash("password123"),
                role=UserRole.ADMIN
            )
            session.add(admin)
        else:
            print(f"Admin user exists: {admin_email}")
            # Ensure password is correct (reset it just in case)
            admin.password_hash = get_password_hash("password123")
            session.add(admin)

        # 2. Ensure Candidate Exists
        candidate_email = "candidate@test.com"
        candidate = session.exec(select(User).where(User.email == candidate_email)).first()
        
        if not candidate:
            print(f"Creating candidate user: {candidate_email}")
            candidate = User(
                email=candidate_email,
                full_name="Test Candidate",
                password_hash=get_password_hash("password123"),
                role=UserRole.CANDIDATE
            )
            session.add(candidate)
        else:
            print(f"Candidate user exists: {candidate_email}")
            candidate.password_hash = get_password_hash("password123")
            session.add(candidate)
            
        session.commit()
        print("Test users setup complete.")

if __name__ == "__main__":
    setup_test_users()
