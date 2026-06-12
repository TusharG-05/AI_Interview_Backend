import requests
import json
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole, InterviewSession, InterviewStatus, Questions
from app.auth.security import get_password_hash, create_access_token

BASE_URL = "http://localhost:7427"

def test_flow():
    with Session(engine) as db:
        # Get admin
        admin_email = "admin@test.com"
        admin_user = db.exec(select(User).where(User.email == admin_email)).first()
        
        # Get candidate
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
        
        # Create a fresh interview session
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
        print(f"Created Interview Session: {session_obj.id}")
        
        # Create token
        token = create_access_token(data={"sub": candidate_user.email, "role": candidate_user.role})
        
        # We need a question to answer
        question = db.exec(select(Questions).where(Questions.marks == 3)).first()
        if not question:
            question = db.exec(select(Questions)).first()
        print(f"Using Question: {question.id} (Marks: {question.marks})")

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Test Evaluate Answer API
    print("\n--- 1. Testing /evaluate-answer ---")
    eval_payload = {
        "question": question.question_text,
        "answer": "This is a partially correct answer to the question.",
        "question_id": question.id
    }
    
    res = requests.post(f"{BASE_URL}/api/interview/evaluate-answer", json=eval_payload, headers=headers)
    print("Evaluate Status Code:", res.status_code)
    eval_data = res.json()
    print("Evaluate Response:", json.dumps(eval_data, indent=2))
    
    if res.status_code != 200:
        print("Failed to evaluate, exiting.")
        return

    # Extract score correctly simulating the frontend
    score = eval_data.get("data", {}).get("score", 0)
    score_out_of_10 = eval_data.get("data", {}).get("score_out_of_10", 0)
    feedback = eval_data.get("data", {}).get("feedback", "")
    
    print(f"\nFrontend parsed -> score: {score}, score_out_of_10: {score_out_of_10}")
    
    # 2. Test Submit Answer API
    print("\n--- 2. Testing /submit-answer-text ---")
    submit_payload = {
        "interview_id": session_obj.id,
        "question_id": question.id,
        "answer_text": "This is a partially correct answer to the question.",
        "feedback": feedback,
        "score": score
    }
    
    res2 = requests.post(f"{BASE_URL}/api/interview/submit-answer-text", data=submit_payload, headers=headers)
    print("Submit Status Code:", res2.status_code)
    print("Submit Response:", json.dumps(res2.json(), indent=2))
    
    # 3. Test Finish Interview API
    print("\n--- 3. Testing /finish ---")
    res3 = requests.post(f"{BASE_URL}/api/interview/finish/{session_obj.id}", headers=headers)
    print("Finish Status Code:", res3.status_code)
    print("Finish Response:", json.dumps(res3.json(), indent=2))
    
    print("\n--- 4. Checking Final DB Results ---")
    import time
    time.sleep(4) # Give background task time to finish evaluation
    
    with Session(engine) as db:
        from app.models.db_models import InterviewResult, Answers
        result = db.exec(select(InterviewResult).where(InterviewResult.interview_id == session_obj.id)).first()
        if result:
            ans = db.exec(select(Answers).where(Answers.interview_result_id == result.id)).first()
            if ans:
                print(f"DB Answer Score: {ans.score}")
                print(f"DB Answer Feedback: {ans.feedback}")
            print(f"DB Total Score: {result.total_score}")
        else:
            print("No result found in DB.")

if __name__ == '__main__':
    test_flow()
