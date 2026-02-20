
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import User, UserRole, QuestionPaper, Questions, InterviewSession, InterviewResult, Answers
from app.auth.security import get_password_hash
from datetime import datetime, timedelta

def seed_data():
    try:
        with Session(engine) as session:
            # 1. Admin (already exists)
            admin = session.exec(select(User).where(User.email == "admin@example.com")).first()
            if not admin:
                # Create if missed
                admin = User(email="admin@example.com", full_name="Admin", password_hash=get_password_hash("admin123"), role=UserRole.ADMIN)
                session.add(admin)
                session.commit()
                session.refresh(admin)

            # 2. Candidate
            candidate_email = "candidate@example.com"
            candidate = session.exec(select(User).where(User.email == candidate_email)).first()
            if not candidate:
                candidate = User(email=candidate_email, full_name="Candidate Doe", password_hash=get_password_hash("pass123"), role=UserRole.CANDIDATE)
                session.add(candidate)
                session.commit()
                session.refresh(candidate)

            # 3. Paper
            paper = session.exec(select(QuestionPaper).where(QuestionPaper.name == "Test Paper")).first()
            if not paper:
                paper = QuestionPaper(name="Test Paper", description="For testing", admin_id=admin.id)
                session.add(paper)
                session.commit()
                session.refresh(paper)
            
            # 4. Question
            question = session.exec(select(Questions).where(Questions.content == "What is Python?")).first()
            if not question:
                question = Questions(paper_id=paper.id, content="What is Python?", question_text="What is Python?", topic="General", difficulty="Easy", marks=5)
                session.add(question)
                session.commit()
                session.refresh(question)

            # 5. Session
            # Check for existing session for this paper
            interview = session.exec(select(InterviewSession).where(InterviewSession.paper_id == paper.id)).first()
            if not interview:
                interview = InterviewSession(
                    admin_id=admin.id,
                    candidate_id=candidate.id,
                    paper_id=paper.id,
                    schedule_time=datetime.utcnow(),
                    max_questions=1,
                    status="completed",
                    total_score=5.0,
                    is_completed=True
                )
                session.add(interview)
                session.commit()
                session.refresh(interview)
                
                # 6. Result
                result = InterviewResult(interview_id=interview.id, total_score=5.0)
                session.add(result)
                session.commit()
                session.refresh(result)
                
                # 7. Answer
                answer = Answers(
                    interview_result_id=result.id,
                    question_id=question.id,
                    candidate_answer="A programming language",
                    score=1.0,
                    feedback="Correct"
                )
                session.add(answer)
                session.commit()
                print("Seeded new interview data.")
            else:
                 # Check if result exists
                 if not interview.result:
                     result = InterviewResult(interview_id=interview.id, total_score=5.0)
                     session.add(result)
                     session.commit()
                     session.refresh(result)
                     
                     answer = Answers(
                        interview_result_id=result.id,
                        question_id=question.id,
                        candidate_answer="A programming language",
                        score=1.0,
                        feedback="Correct"
                    )
                     session.add(answer)
                     session.commit()
                     print("Added missing result/answer to existing session.")
                 else:
                     print("Interview data already exists.")
    except Exception as e:
        print(f"Error seeding data: {e}")

if __name__ == "__main__":
    seed_data()
