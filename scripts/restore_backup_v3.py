import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to sys.path to import app modules
sys.path.append(os.getcwd())

from sqlmodel import Session, select, create_all, SQLModel
from app.core.database import engine
from app.models.db_models import User, Team, QuestionPaper, Questions, InterviewSession, InterviewResult, Answers, UserRole

BACKUP_FILE = "backups/backup_20260303_172805.json"

def restore_data():
    print(f"Starting restoration from {BACKUP_FILE}...")
    
    if not os.path.exists(BACKUP_FILE):
        print(f"Error: Backup file {BACKUP_FILE} not found.")
        return

    with open(BACKUP_FILE, "r") as f:
        backup = json.load(f)

    data = backup.get("data", {})
    
    # 1. Reset Database Schema
    print("Dropping and recreating all tables...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 2. Create Default Teams
        print("Creating default teams...")
        super_team = Team(name="SUPER_ADMIN", description="Global Super Admin Team")
        other_team = Team(name="Other", description="Default team for restored users")
        session.add(super_team)
        session.add(other_team)
        session.commit()
        session.refresh(super_team)
        session.refresh(other_team)

        # 3. Restore Users
        print(f"Restoring {len(data.get('user', []))} users...")
        user_mapping = {} # old_id -> new_user_obj
        for u_data in data.get("user", []):
            role_val = u_data.get("role")
            role = UserRole(role_val) if role_val else UserRole.CANDIDATE
            
            # Map super admins to SUPER_ADMIN team, others to Other
            target_team_id = super_team.id if role == UserRole.SUPER_ADMIN else other_team.id
            
            new_user = User(
                # id=u_data.get("id"), # Let DB auto-assign to avoid PK conflicts if any, but mapping needs old IDs
                email=u_data.get("email"),
                full_name=u_data.get("full_name"),
                password_hash=u_data.get("password_hash"),
                role=role,
                resume_text=u_data.get("resume_text"),
                profile_image=u_data.get("profile_image"),
                face_embedding=u_data.get("face_embedding"),
                team_id=target_team_id
            )
            session.add(new_user)
            user_mapping[u_data.get("id")] = new_user

        session.commit()
        for u in user_mapping.values():
            session.refresh(u)

        # 4. Restore Question Papers
        print(f"Restoring {len(data.get('questionpaper', []))} question papers...")
        paper_mapping = {} # old_id -> new_paper_obj
        for p_data in data.get("questionpaper", []):
            admin_id = p_data.get("adminUser")
            new_admin = user_mapping.get(admin_id)
            
            new_paper = QuestionPaper(
                name=p_data.get("name"),
                description=p_data.get("description", ""),
                adminUser=new_admin.id if new_admin else None,
                question_count=p_data.get("question_count", 0),
                total_marks=p_data.get("total_marks", 0),
                created_at=datetime.fromisoformat(p_data.get("created_at")) if p_data.get("created_at") else datetime.utcnow()
            )
            session.add(new_paper)
            paper_mapping[p_data.get("id")] = new_paper

        session.commit()
        for p in paper_mapping.values():
            session.refresh(p)

        # 5. Restore Questions
        print(f"Restoring {len(data.get('questions', []))} questions...")
        question_mapping = {} # old_id -> new_q_obj
        for q_data in data.get("questions", []):
            old_paper_id = q_data.get("paper_id")
            new_paper = paper_mapping.get(old_paper_id)
            if not new_paper:
                continue
            
            new_q = Questions(
                paper_id=new_paper.id,
                content=q_data.get("content"),
                question_text=q_data.get("question_text"),
                topic=q_data.get("topic", "General"),
                difficulty=q_data.get("difficulty", "Medium"),
                marks=q_data.get("marks", 1),
                response_type=q_data.get("response_type", "audio")
            )
            session.add(new_q)
            question_mapping[q_data.get("id")] = new_q
        
        session.commit()
        for q in question_mapping.values():
            session.refresh(q)

        # 6. Restore Interview Sessions
        print(f"Restoring {len(data.get('interviewsession', []))} interview sessions...")
        session_mapping = {}
        for s_data in data.get("interviewsession", []):
            old_candidate_id = s_data.get("candidate_id")
            old_admin_id = s_data.get("admin_id")
            old_paper_id = s_data.get("paper_id")
            
            new_candidate = user_mapping.get(old_candidate_id)
            new_admin = user_mapping.get(old_admin_id)
            new_paper = paper_mapping.get(old_paper_id)
            
            if not new_candidate or not new_paper:
                continue
                
            new_s = InterviewSession(
                # access_token=s_data.get("access_token"),
                admin_id=new_admin.id if new_admin else 0,
                candidate_id=new_candidate.id,
                paper_id=new_paper.id,
                team_id=new_candidate.team_id,
                status=s_data.get("status", "scheduled"),
                schedule_time=datetime.fromisoformat(s_data.get("schedule_time")) if s_data.get("schedule_time") else None,
                duration_minutes=s_data.get("duration_minutes", 60),
                interview_round=s_data.get("interview_round")
            )
            # Use specific access token if it works
            new_s.access_token = s_data.get("access_token")
            session.add(new_s)
            session_mapping[s_data.get("id")] = new_s

        session.commit()
        for s in session_mapping.values():
            session.refresh(s)

        # 7. Restore Results
        print(f"Restoring {len(data.get('interviewresult', []))} results...")
        result_mapping = {}
        for r_data in data.get("interviewresult", []):
            old_session_id = r_data.get("interview_session_id")
            new_session = session_mapping.get(old_session_id)
            if not new_session:
                continue
                
            new_r = InterviewResult(
                interview_session_id=new_session.id,
                total_score=r_data.get("total_score"),
                status=r_data.get("status", "PENDING"),
                summary=r_data.get("summary"),
                ai_feedback=r_data.get("ai_feedback")
            )
            session.add(new_r)
            result_mapping[r_data.get("id")] = new_r

        session.commit()
        for r in result_mapping.values():
            session.refresh(r)

        # 8. Restore Answers
        print(f"Restoring {len(data.get('answers', []))} answers...")
        for a_data in data.get("answers", []):
            old_result_id = a_data.get("interview_result_id")
            old_question_id = a_data.get("question_id")
            
            new_result = result_mapping.get(old_result_id)
            new_question = question_mapping.get(old_question_id)
            
            if not new_result or not new_question:
                continue
            
            new_a = Answers(
                interview_result_id=new_result.id,
                question_id=new_question.id,
                candidate_answer=a_data.get("candidate_answer"),
                feedback=a_data.get("feedback"),
                score=a_data.get("score", 0.0),
                audio_path=a_data.get("audio_path"),
                transcribed_text=a_data.get("transcribed_text")
            )
            session.add(new_a)
        
        session.commit()

        print("Restoration complete!")

if __name__ == "__main__":
    restore_data()
