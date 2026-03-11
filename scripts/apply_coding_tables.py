"""
Direct creation of new coding question tables, bypassing
the broken Alembic multi-head chain.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import DATABASE_URL
from app.core.database import engine
import sqlalchemy as sa

print(f"Using DB: {DATABASE_URL[:30]}...")

with engine.connect() as conn:
    inspector = sa.inspect(engine)
    existing = inspector.get_table_names()
    print(f"Existing tables: {[t for t in existing if 'coding' in t.lower() or 'interview' in t.lower()]}")

    # 1. Create codingquestionpaper if not exists
    if 'codingquestionpaper' not in existing:
        conn.execute(sa.text("""
            CREATE TABLE codingquestionpaper (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR NOT NULL DEFAULT '',
                "adminUser" INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
                question_count INTEGER NOT NULL DEFAULT 0,
                total_marks INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                team_id INTEGER REFERENCES team(id) ON DELETE SET NULL
            )
        """))
        conn.execute(sa.text('CREATE INDEX ix_codingquestionpaper_name ON codingquestionpaper (name)'))
        print("  Created: codingquestionpaper")
    else:
        print("  Skipped: codingquestionpaper (already exists)")

    # 2. Create codingquestions if not exists
    if 'codingquestions' not in existing:
        conn.execute(sa.text("""
            CREATE TABLE codingquestions (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES codingquestionpaper(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL DEFAULT '',
                problem_statement VARCHAR NOT NULL DEFAULT '',
                examples VARCHAR NOT NULL DEFAULT '[]',
                constraints VARCHAR NOT NULL DEFAULT '[]',
                starter_code VARCHAR NOT NULL DEFAULT '',
                topic VARCHAR NOT NULL DEFAULT 'Algorithms',
                difficulty VARCHAR NOT NULL DEFAULT 'Medium',
                marks INTEGER NOT NULL DEFAULT 6
            )
        """))
        print("  Created: codingquestions")
    else:
        print("  Skipped: codingquestions (already exists)")

    # 3. Add coding_paper_id to interviewsession if not present
    col_names = [c['name'] for c in inspector.get_columns('interviewsession')]
    if 'coding_paper_id' not in col_names:
        conn.execute(sa.text("""
            ALTER TABLE interviewsession
            ADD COLUMN coding_paper_id INTEGER REFERENCES codingquestionpaper(id) ON DELETE SET NULL
        """))
        print("  Added column: interviewsession.coding_paper_id")
    else:
        print("  Skipped: coding_paper_id (already exists)")

    # 4. Make paper_id nullable in interviewsession
    # Postgres: alter column
    try:
        conn.execute(sa.text("ALTER TABLE interviewsession ALTER COLUMN paper_id DROP NOT NULL"))
        print("  Made nullable: interviewsession.paper_id")
    except Exception as e:
        print(f"  paper_id nullable: {e}")

    conn.commit()

print("Done.")
