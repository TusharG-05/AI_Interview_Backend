from sqlmodel import Session, text
from app.core.database import engine

def fix_enum():
    with Session(engine) as db:
        try:
            db.exec(text("ALTER TYPE interviewstatus ADD VALUE 'SUSPENDED'"))
            db.commit()
            print("Successfully added SUSPENDED to interviewstatus enum")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_enum()
