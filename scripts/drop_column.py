from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/interview_db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Dropping column resume_filename from table 'user'...")
    try:
        conn.execute(text("ALTER TABLE \"user\" DROP COLUMN IF EXISTS resume_filename"))
        conn.commit()
        print("Column dropped successfully (or did not exist).")
    except Exception as e:
        print(f"Error dropping column: {e}")
