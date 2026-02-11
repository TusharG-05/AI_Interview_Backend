import json
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the app directory
sys.path.append(os.getcwd())
load_dotenv()

from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.db_models import Question

QUESTIONS_FILE = "app/assets/questions.json"

def migrate_questions():
    print("Starting question migration...")
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing DB: {e}")
        return
    
    if not os.path.exists(QUESTIONS_FILE):
        print(f"No questions file found at {QUESTIONS_FILE}")
        return

    try:
        with open(QUESTIONS_FILE, 'r') as f:
            data = json.load(f)
            questions = data if isinstance(data, list) else data.get('questions', [])
    except Exception as e:
        print(f"Error reading questions file: {e}")
        return

    try:
        with Session(engine) as session:
            count = 0
            for q_data in questions:
                # Check if exists
                stmt = select(Question).where(Question.content == q_data['question'])
                existing = session.exec(stmt).first()
                
                if not existing:
                    new_q = Question(
                        content=q_data['question'],
                        topic=q_data.get('topic', 'General'),
                        difficulty=q_data.get('difficulty', 'Medium')
                    )
                    session.add(new_q)
                    count += 1
            
            if count > 0:
                session.commit()
                print(f"Successfully migrated {count} new questions.")
            else:
                print("No new questions to migrate.")
                
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_questions()
