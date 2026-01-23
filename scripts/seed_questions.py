from sqlmodel import Session, select
from config.database import engine, create_db_and_tables
from models.db_models import Question

def seed_questions():
    with Session(engine) as session:
        # Check if questions exist
        existing = session.exec(select(Question)).first()
        if existing:
            print("Questions already exist in the database.")
            return

        print("Seeding default questions...")
        questions = [
            Question(content="Explain the difference between a process and a thread.", topic="Operating Systems", difficulty="Medium"),
            Question(content="What is ACID in database systems? Explain each property.", topic="Databases", difficulty="Medium"),
            Question(content="Describe the concept of RESTful APIs.", topic="Web Development", difficulty="Easy"),
            Question(content="How does garbage collection work in Python (or your preferred language)?", topic="Programming Languages", difficulty="Hard"),
            Question(content="Explain the time complexity of QuickSort in the worst usage.", topic="Algorithms", difficulty="Medium")
        ]
        
        for q in questions:
            session.add(q)
        
        session.commit()
        print(f"Successfully added {len(questions)} questions.")

if __name__ == "__main__":
    create_db_and_tables()
    seed_questions()
