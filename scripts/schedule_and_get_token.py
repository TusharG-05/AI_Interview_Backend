import uuid
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, QuestionPaper, InterviewSession, InterviewStatus, CandidateStatus, SessionQuestion, Questions, InterviewRound

def schedule_interview():
    # Configuration
    ADMIN_ID = 6
    CANDIDATE_ID = 82
    PAPER_ID = 84
    
    with Session(engine) as session:
        # 1. Verify entities exist
        admin = session.get(User, ADMIN_ID)
        candidate = session.get(User, CANDIDATE_ID)
        paper = session.get(QuestionPaper, PAPER_ID)
        
        if not admin:
            print(f"Error: Admin with ID {ADMIN_ID} not found.")
            return
        if not candidate:
            print(f"Error: Candidate with ID {CANDIDATE_ID} not found.")
            return
        if not paper:
            print(f"Error: Paper with ID {PAPER_ID} not found.")
            return

        # 2. Create InterviewSession
        # Match the logic in app/routers/admin.py
        now = datetime.now(timezone.utc)
        access_token = uuid.uuid4().hex
        
        new_session = InterviewSession(
            admin_id=ADMIN_ID,
            candidate_id=CANDIDATE_ID,
            paper_id=PAPER_ID,
            interview_round=InterviewRound.ROUND_1,
            schedule_time=now,
            duration_minutes=1440,
            max_questions=0,
            status=InterviewStatus.SCHEDULED,
            current_status=CandidateStatus.INVITED,
            last_activity=now,
            warning_count=0,
            max_warnings=3,
            is_suspended=False,
            is_completed=False,
            allow_copy_paste=False,
            access_token=access_token
        )
        
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        
        # 3. Assign questions (as done in admin.py)
        available_questions = session.exec(
            select(Questions).where(Questions.paper_id == PAPER_ID)
        ).all()
        
        for idx, question in enumerate(available_questions):
            session_question = SessionQuestion(
                interview_id=new_session.id,
                question_id=question.id,
                sort_order=idx
            )
            session.add(session_question)
        
        session.commit()
        
        print(f"SUCCESS: Interview scheduled.")
        print(f"Interview ID: {new_session.id}")
        print(f"Access Token: {new_session.access_token}")
        print(f"Candidate: {candidate.email}")
        print(f"Paper: {paper.name}")

if __name__ == "__main__":
    schedule_interview()
