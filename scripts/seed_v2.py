from app.models.db_models import User, UserRole, Team
from app.auth.security import get_password_hash
from app.core.database import engine
from sqlmodel import Session, select
from datetime import datetime, timezone

def seed():
    with Session(engine) as session:
        # 1. Create Super Admin
        sa = session.exec(select(User).where(User.email == "admin@test.com")).first()
        if not sa:
            sa = User(
                email="admin@test.com", 
                password_hash=get_password_hash("admin123"), 
                full_name="Super Admin", 
                role=UserRole.SUPER_ADMIN
            )
            session.add(sa)
            session.commit()
            session.refresh(sa)
            print(f"Created Super Admin: {sa.email}")
        else:
            print(f"Super Admin already exists: {sa.email}")

        # 2. Create Default Team
        team = session.exec(select(Team).where(Team.name == "Main Team")).first()
        if not team:
            team = Team(
                name="Main Team",
                description="Default team for v2",
                created_by=sa.id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(team)
            session.commit()
            session.refresh(team)
            print(f"Created Team: {team.name}")
        else:
            print(f"Team already exists: {team.name}")

        # 3. Create Candidate
        cand = session.exec(select(User).where(User.email == "candidate@test.com")).first()
        if not cand:
            cand = User(
                email="candidate@test.com", 
                password_hash=get_password_hash("candidate123"), 
                full_name="Test Candidate", 
                role=UserRole.CANDIDATE
            )
            session.add(cand)
            session.commit()
            print(f"Created Candidate: {cand.email}")
        else:
            print(f"Candidate already exists: {cand.email}")

        print("\n✅ Seeding for v2 completed successfully.")

if __name__ == "__main__":
    seed()
