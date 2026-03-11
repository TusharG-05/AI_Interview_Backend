import os
import sys

# Add the project root to sys.path so we can import app modules
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Team, QuestionPaper, InterviewSession

def cleanup_teams():
    print("🚀 Starting cleanup of all teams and associated records...")
    
    with Session(engine) as session:
        # 1. Fetch all teams
        teams = session.exec(select(Team)).all()
        
        if not teams:
            print("✅ No teams found to delete.")
            return

        print(f"📦 Found {len(teams)} teams. Deleting...")
        
        for team in teams:
            team_id = team.id
            team_name = team.name
            
            # In the new architecture, teams group users.
            # team_id is no longer on QuestionPaper or InterviewSession.
            # We just need to delete the team. Users will have team_id set to NULL by DB (SET NULL).
            
            print(f"🗑️ Deleting Team: '{team_name}' (ID: {team_id})")
            session.delete(team)
            
        # 5. Commit all changes
        try:
            session.commit()
            print("✨ All teams deleted successfully! (Users unassigned automatically)")
        except Exception as e:
            session.rollback()
            print(f"❌ Error during deletion: {e}")

if __name__ == "__main__":
    cleanup_teams()
