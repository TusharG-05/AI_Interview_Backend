from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash
from app.core.database import engine
from sqlmodel import Session, select

def seed():
    with Session(engine) as session:
        a = session.exec(select(User).where(User.email == "admin@test.com")).first()
        if not a:
            a = User(email="admin@test.com", password_hash=get_password_hash("admin123"), full_name="Admin", role=UserRole.ADMIN)
            session.add(a)

        c = session.exec(select(User).where(User.email == "sakshamc1@test.com")).first()
        if not c:
            c = User(email="sakshamc1@test.com", password_hash=get_password_hash("candidate123"), full_name="Candidate", role=UserRole.CANDIDATE)
            session.add(c)
        session.commit()
        print("Seeded successfully")

if __name__ == "__main__":
    seed()
