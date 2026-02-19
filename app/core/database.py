from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import DATABASE_URL

# Configure connection args based on database type
engine_args = {}
connect_args = {}

if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    engine_args = {"pool_pre_ping": True}

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_args)

def init_db():
    from ..models.db_models import (
        User, QuestionPaper, Questions, 
        InterviewSession, InterviewResult, Answers,
        SessionQuestion, ProctoringEvent
    )
    import logging
    logger = logging.getLogger("uvicorn")
    try:
        # 1. Base table creation (SQLModel)
        SQLModel.metadata.create_all(engine)
        
        # 2. Programmatic migrations (Alembic)
        try:
            from alembic import command
            from alembic.config import Config
            import os
            
            # Ensure we are in the right directory to find alembic.ini
            alembic_cfg = Config("alembic.ini")
            # Force Database URL from environment for migrations
            alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
            
            logger.info("Database: Running migrations (alembic upgrade head)...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database: Migrations complete.")
        except Exception as migration_e:
            logger.warning(f"Database migration notice (ignored if DB is fresh): {migration_e}")

    except Exception as e:
        # Gracefully handle race conditions when multiple workers attempt creation simultaneously
        logger.warning(f"Database initialization notice: {e}")

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
