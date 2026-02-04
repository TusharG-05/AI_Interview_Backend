import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
from app.core.database import engine, init_db

def fix_schema():
    print("Fixing Schema...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS interviewsession"))
        conn.commit()
    print("Dropped 'interviewsession' table.")
    
    # Re-init to create it
    init_db()
    print("Re-initialized DB (Created missing tables).")

if __name__ == "__main__":
    fix_schema()
