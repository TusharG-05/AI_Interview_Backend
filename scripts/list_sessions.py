import sys
import os
from dotenv import load_dotenv

# Ensure we can import from the app directory
sys.path.append(os.getcwd())
load_dotenv()

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import InterviewSession

def list_sessions():
    try:
        with Session(engine) as session:
            sessions = session.exec(select(InterviewSession)).all()

            if not sessions:
                print("No interview sessions found in the database.")
                return

            print(f"\n{'ID':<5} {'Access Token':<35} {'AdminID':<10} {'Status':<12}")
            print("-" * 65)
            for s in sessions:
                print(f"{s.id:<5} {s.access_token:<35} {s.admin_id:<10} {s.status:<12}")
            print("-" * 65 + "\n")
            
    except Exception as e:
        print(f"Error connecting to database or listing sessions: {e}")

if __name__ == "__main__":
    list_sessions()
