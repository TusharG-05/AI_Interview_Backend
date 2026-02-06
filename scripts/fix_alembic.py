from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

# Fix for "postgres://" deprecated in SQLAlchemy 1.4+ (if present)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    try:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()
        print("Successfully cleared alembic_version table.")
    except Exception as e:
        print(f"Error clearing table (maybe it doesn't exist?): {e}")
