from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import InterviewRoom, InterviewSession, InterviewResponse

with Session(engine) as session:
    room_id = 1
    room = session.get(InterviewRoom, room_id)

    if not room:
        print(f"Room {room_id} not found.")
    else:
        print(f"Found room {room.room_code}. Deleting related sessions...")
        
        # Get sessions
        sessions = session.exec(select(InterviewSession).where(InterviewSession.room_id == room_id)).all()
        for s in sessions:
            # Delete responses for this session first
            responses = session.exec(select(InterviewResponse).where(InterviewResponse.session_id == s.id)).all()
            for r in responses:
                session.delete(r)
            
            session.delete(s)
        
        print("Sessions deleted. Deleting room...")
        session.delete(room)
        session.commit()
        print("Room deleted successfully.")
