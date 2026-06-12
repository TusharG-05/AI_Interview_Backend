import asyncio
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import InterviewSession, InterviewResult, Answers
from app.tasks.interview_tasks import process_session_results
from app.models.db_models import User
from app.auth.security import create_access_token

def run():
    admin_id = None
    with Session(engine) as db:
        # Get session 619
        session_obj = db.get(InterviewSession, 619)
        if not session_obj:
            print("Session 619 not found.")
            return
        admin_id = session_obj.admin_id

        result_obj = db.exec(select(InterviewResult).where(InterviewResult.interview_id == 619)).first()
        if not result_obj:
            print("Result not found.")
            return

        # Fetch all answers
        answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
        
        print("Clearing scores for re-evaluation...")
        for ans in answers:
            if ans.candidate_answer != "Candidate skipped the question." and ans.candidate_answer:
                ans.score = 0.0
                ans.feedback = ""
                db.add(ans)
        
        # Also reset result status to PENDING so process_session_results processes it
        result_obj.result_status = "PENDING"
        db.add(result_obj)
        db.commit()

        print("Running process_session_results...")
    
    # Run the processing task (which creates its own DB session)
    process_session_results(619)
    
    print("Done. Fetching API response...")
    with Session(engine) as db:
        # Get admin user
        admin = db.get(User, admin_id)
        
    import requests
    token = create_access_token(data={"sub": admin.email, "role": admin.role})
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"http://localhost:7427/api/admin/results/619", headers=headers)
    
    if res.status_code == 200:
        with open("reval_output.json", "w") as f:
            json.dump(res.json(), f, indent=2)
        print("Response saved to reval_output.json")
    else:
        print("Failed to fetch details:", res.status_code, res.text)

if __name__ == "__main__":
    run()
