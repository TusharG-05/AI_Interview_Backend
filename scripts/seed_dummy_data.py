import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.db_models import (
    User, UserRole, QuestionPaper, Questions, 
    InterviewSession, InterviewStatus, CandidateStatus
)
from app.auth.security import get_password_hash
import uuid

def seed_data():
    with Session(engine) as session:
        print("Seeding Users...")
        
        # 1. Super Admin
        admin_email = "admin@test.com"
        admin = session.exec(select(User).where(User.email == admin_email)).first()
        if not admin:
            admin = User(
                email=admin_email,
                full_name="Super Admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"Created Admin: {admin.email} (ID: {admin.id})")
        else:
            print(f"Admin already exists: {admin.email}")

        # 2. Candidates
        candidates_data = [
            ("Aarav Sharma", "aarav@example.com"),
            ("Vihaan Gupta", "vihaan@example.com"),
            ("Aditya Verma", "aditya@example.com"),
            ("Ananya Iyer", "ananya@example.com"),
            ("Diya Nair", "diya@example.com"),
        ]
        
        candidates = []
        for name, email in candidates_data:
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                user = User(
                    email=email,
                    full_name=name,
                    password_hash=get_password_hash("password123"),
                    role=UserRole.CANDIDATE
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"Created Candidate: {user.email}")
            else:
                print(f"Candidate already exists: {user.email}")
            candidates.append(user)

        # 3. Question Papers
        print("\nSeeding Question Papers & Questions...")
        
        paper_data = [
            ("Python Mastery", "Advanced Python concepts for senior developers."),
            ("System Design", "Scalable architecture and distributed systems."),
            ("Behavioral Fit", "HR and cultural fit assessment.")
        ]
        
        papers = []
        for name, desc in paper_data:
            paper = session.exec(select(QuestionPaper).where(QuestionPaper.name == name)).first()
            if not paper:
                paper = QuestionPaper(
                    name=name,
                    description=desc,
                    admin_id=admin.id
                )
                session.add(paper)
                session.commit()
                session.refresh(paper)
                print(f"Created Paper: {paper.name}")
                
                # Add Questions for this paper
                if name == "Python Mastery":
                    qs = [
                        ("Explain the Global Interpreter Lock (GIL).", "Concurrency", "Hard"),
                        ("What are Python decorators?", "Functions", "Medium"),
                        ("Difference between list and tuple?", "Data Structures", "Easy"),
                    ]
                elif name == "System Design":
                    qs = [
                        ("Design a URL shortener like bit.ly", "System Design", "Hard"),
                        ("Explain CAP theorem.", "Distributed Systems", "Medium"),
                    ]
                else:
                    qs = [
                        ("Tell me about a time you failed.", "HR", "Medium"),
                        ("Where do you see yourself in 5 years?", "HR", "Easy"),
                    ]
                
                for content, topic, diff in qs:
                    q = Questions(
                        paper_id=paper.id,
                        content=content,
                        topic=topic,
                        difficulty=diff,
                        response_type="audio"
                    )
                    session.add(q)
                session.commit()
            else:
                print(f"Paper already exists: {paper.name}")
            papers.append(paper)

        # 4. Interview Sessions
        print("\nSeeding Interview Sessions...")
        
        # Scenario A: Scheduled (Future)
        s1 = session.exec(select(InterviewSession).where(InterviewSession.candidate_id == candidates[0].id)).first()
        if not s1:
            s1 = InterviewSession(
                admin_id=admin.id,
                candidate_id=candidates[0].id,
                paper_id=papers[0].id,
                schedule_time=datetime.utcnow() + timedelta(days=1),
                status=InterviewStatus.SCHEDULED,
                current_status=CandidateStatus.INVITED,
                admin_name=admin.full_name,
                candidate_name=candidates[0].full_name
            )
            session.add(s1)
            print(f"Scheduled Interview for {candidates[0].full_name}")

        # Scenario B: Completed (Past)
        s2 = session.exec(select(InterviewSession).where(InterviewSession.candidate_id == candidates[1].id)).first()
        if not s2:
            s2 = InterviewSession(
                admin_id=admin.id,
                candidate_id=candidates[1].id,
                paper_id=papers[1].id,
                schedule_time=datetime.utcnow() - timedelta(days=2),
                start_time=datetime.utcnow() - timedelta(days=2),
                end_time=datetime.utcnow() - timedelta(days=2, hours=-1),
                status=InterviewStatus.COMPLETED,
                current_status=CandidateStatus.INTERVIEW_COMPLETED,
                total_score=85.5,
                admin_name=admin.full_name,
                candidate_name=candidates[1].full_name
            )
            session.add(s2)
            print(f"Completed Interview for {candidates[1].full_name}")

        # Scenario C: Live (Now)
        s3 = session.exec(select(InterviewSession).where(InterviewSession.candidate_id == candidates[2].id)).first()
        if not s3:
            s3 = InterviewSession(
                admin_id=admin.id,
                candidate_id=candidates[2].id,
                paper_id=papers[0].id,
                schedule_time=datetime.utcnow(),
                start_time=datetime.utcnow(),
                status=InterviewStatus.LIVE,
                current_status=CandidateStatus.INTERVIEW_ACTIVE,
                admin_name=admin.full_name,
                candidate_name=candidates[2].full_name
            )
            session.add(s3)
            print(f"Live Interview for {candidates[2].full_name}")
            
        session.commit()
        print("\nDatabase seeding complete!")

if __name__ == "__main__":
    init_db()
    seed_data()
