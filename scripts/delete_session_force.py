import sys
import os
import argparse
from dotenv import load_dotenv

# Ensure we can import from the app directory
sys.path.append(os.getcwd())
load_dotenv()

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import InterviewSession, InterviewResponse

def delete_session(session_id):
    with Session(engine) as session:
        interview_session = session.get(InterviewSession, session_id)

        if not interview_session:
            print(f"Session {session_id} not found.")
            return

        print(f"Found session '{interview_session.access_token}' (ID: {session_id}). Deleting related data...")
        
        # Delete responses for this session first
        responses = session.exec(select(InterviewResponse).where(InterviewResponse.session_id == session_id)).all()
        if responses:
            print(f"  Deleting {len(responses)} responses...")
            for r in responses:
                session.delete(r)
        
        print("Deleting session...")
        session.delete(interview_session)
        session.commit()
        print(f"✅ Session {session_id} and all associated data deleted successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Force delete an interview session and all associated responses.")
    parser.add_argument("session_id", type=int, help="ID of the session to delete")
    
    args = parser.parse_args()
    
    confirm = input(f"Are you sure you want to delete session {args.session_id}? This cannot be undone. (y/N): ")
    if confirm.lower() == 'y':
        delete_session(args.session_id)
    else:
        print("Operation cancelled.")
