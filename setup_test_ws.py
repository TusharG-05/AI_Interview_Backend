import asyncio
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole, InterviewSession, CandidateStatus, InterviewStatus
from app.auth.security import get_password_hash, create_access_token

def setup_test_data():
    with Session(engine) as db:
        # 1. Get Admin User
        admin_email = "admin@test.com"
        admin_user = db.exec(select(User).where(User.email == admin_email)).first()
        if not admin_user:
            print(f"Error: Admin {admin_email} not found in DB.")
            return

        # 2. Create Candidate User
        candidate_email = "mango@yopmail.com"
        candidate_user = db.exec(select(User).where(User.email == candidate_email)).first()
        if not candidate_user:
            candidate_user = User(
                email=candidate_email,
                name="Mango Test",
                role=UserRole.CANDIDATE,
                hashed_password=get_password_hash("mango@123"),
                is_active=True
            )
            db.add(candidate_user)
            db.commit()
            db.refresh(candidate_user)
            print(f"Created candidate: {candidate_email}")
        else:
            print(f"Candidate {candidate_email} already exists.")

        # 3. Create Interview Session
        # Check if an active one already exists
        session_obj = db.exec(
            select(InterviewSession).where(
                InterviewSession.candidate_id == candidate_user.id,
                InterviewSession.is_completed == False
            )
        ).first()

        if not session_obj:
            now = datetime.now(timezone.utc)
            session_obj = InterviewSession(
                candidate_id=candidate_user.id,
                admin_id=admin_user.id,
                status=InterviewStatus.SCHEDULED,
                schedule_time=now,
                expires_at=now + timedelta(days=1),
                max_warnings=5
            )
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)
            print(f"Created Interview Session: ID {session_obj.id}")
        else:
            print(f"Using existing Interview Session: ID {session_obj.id}")

        # 4. Generate JWT Tokens
        admin_token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
        candidate_token = create_access_token(data={"sub": candidate_user.email, "role": candidate_user.role})

        print("\n" + "="*50)
        print("✅ READY TO TEST ON POSTMAN")
        print("="*50 + "\n")
        
        print("🧑‍💼 ADMIN TAB (Tab 1)")
        print("-" * 30)
        print(f"URL: ws://localhost:7427/api/admin/dashboard/ws?token={admin_token}")
        print("\n")
        
        print(f"🧑‍🎓 CANDIDATE TAB (Tab 2) - Interview ID: {session_obj.id}")
        print("-" * 30)
        print(f"URL: ws://localhost:7427/ws/api/interview/{session_obj.id}?token={candidate_token}")
        print("\n")

if __name__ == "__main__":
    setup_test_data()
