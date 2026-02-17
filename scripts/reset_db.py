
try:
    import psycopg2
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
import os

# Parse DB URL from env or hardcode consistent with .env
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/interview_db
# We need to extract params
DB_HOST = "localhost"
DB_NAME = "interview_db"
DB_USER = "postgres"
DB_PASS = "admin123" # User said "password admin123" earlier

def reset_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop all tables
    print("Dropping public schema...")
    cursor.execute("DROP SCHEMA public CASCADE;")
    cursor.execute("CREATE SCHEMA public;")
    cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
    cursor.execute("GRANT ALL ON SCHEMA public TO public;")
    
    print("Database reset complete.")
    conn.close()

if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        print(f"Error resetting DB: {e}")
