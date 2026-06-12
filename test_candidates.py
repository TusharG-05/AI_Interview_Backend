import asyncio
from app.core.database import get_db, engine
from sqlmodel import Session, select
from app.models.db_models import User, UserRole, InterviewSession
from app.routers.admin import list_candidates

async def main():
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
        try:
            res = await list_candidates(skip=0, limit=20, search=None, current_user=admin, session=session)
            print(res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
