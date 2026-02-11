from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

def seed_users():
    with Session(engine) as session:
        # 1. Super Admin
        admin_email = "admin@test.com"
        existing_admin = session.exec(select(User).where(User.email == admin_email)).first()
        
        if not existing_admin:
            print(f"Creating Super Admin: {admin_email}")
            admin = User(
                email=admin_email,
                full_name="Super Admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN
            )
            session.add(admin)
        else:
            print(f"Admin {admin_email} already exists.")

        # 2. Dummy Candidates
        candidates = [
            ("Aarav Sharma", "aarav@example.com"),
            ("Vihaan Gupta", "vihaan@example.com"),
            ("Aditya Verma", "aditya@example.com"),
            ("Ananya Iyer", "ananya@example.com"),
            ("Diya Nair", "diya@example.com"),
            ("Saanvi Reddy", "saanvi@example.com"),
            ("Ishaan Malhotra", "ishaan@example.com"),
            ("Kabir Singh", "kabir@example.com"),
            ("Rohan Joshi", "rohan@example.com"),
            ("Myra Kapoor", "myra@example.com")
        ]
        
        for name, email in candidates:
            existing = session.exec(select(User).where(User.email == email)).first()
            if not existing:
                print(f"Creating Candidate: {email}")
                user = User(
                    email=email,
                    full_name=name,
                    password_hash=get_password_hash("password123"),
                    role=UserRole.CANDIDATE
                )
                session.add(user)
            else:
                print(f"Candidate {email} already exists.")
        
        session.commit()
        print("User seeding complete!")

if __name__ == "__main__":
    init_db()
    seed_users()
