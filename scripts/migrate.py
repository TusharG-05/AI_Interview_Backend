import json
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from config.database import engine, create_db_and_tables
from models.db_models import Question

QUESTIONS_FILE = "config/questions.json"

def migrate_questions():
    print("Starting migration...")
    create_db_and_tables()
    
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
