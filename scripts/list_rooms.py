from sqlmodel import select
from config.database import get_session
from models.db_models import InterviewRoom, User

# Manually get session
session_generator = get_session()
session = next(session_generator)

rooms = session.exec(select(InterviewRoom)).all()

print(f"{'ID':<5} {'Code':<10} {'AdminID':<10} {'Active':<10} {'MaxSessions':<15}")
print("-" * 60)
for room in rooms:
    print(f"{room.id:<5} {room.room_code:<10} {room.admin_id:<10} {room.is_active:<10} {room.max_sessions:<15}")
