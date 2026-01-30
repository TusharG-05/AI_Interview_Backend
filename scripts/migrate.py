import json
import os
import sys

# Add parent directory to path to import modules
from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.db_models import Question

QUESTIONS_FILE = "app/assets/questions.json"

def migrate_questions():
    print("Starting migration...")
    init_db()
    
    if not os.path.exists(QUESTIONS_FILE):
        print(f"No questions file found at {QUESTIONS_FILE}")
        return

    with open(QUESTIONS_FILE, 'r') as f:
        data = json.load(f)
        questions = data if isinstance(data, list) else data.get('questions', [])

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
        
        session.commit()
        print(f"Migrated {count} new questions.")

if __name__ == "__main__":
    migrate_questions()
