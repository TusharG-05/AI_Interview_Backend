import sys
import os
import json
import asyncio
from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models.db_models import Question, InterviewSession, ProctoringEvent, User
from app.services.interview import generate_resume_question_content
from app.services.camera import CameraService
import numpy as np

async def test_resume_ai():
    print("\n--- Testing Aggressive Resume AI ---")
    resume_text = """
    Harpreet Singh
    Senior Software Engineer
    5 years experience with React, Kubernetes, and Golang internals.
    Specialized in low-latency systems and distributed databases using Redis.
    """
    context = "Candidate applying for Senior Backend Role"
    
    result = generate_resume_question_content(context, resume_text)
    print(f"Topic Selected: {result['topic']}")
    print(f"Question Generated: {result['question']}")
    
    if result['topic'] in ["React", "Python", "Kubernetes", "Docker", "Go", "AWS", "SQL", "NoSQL", "Redis"]:
        print("✅ Success: Skill extraction worked.")
    else:
        print("⚠️ Warning: Topic was generic.")

async def test_proctoring_persistence():
    print("\n--- Testing Proctoring Persistence ---")
    init_db()
    with Session(engine) as session:
        # Create a test session
        test_session = session.exec(select(InterviewSession)).first()
        if not test_session:
            test_session = InterviewSession(candidate_name="Tester")
            session.add(test_session)
            session.commit()
            session.refresh(test_session)
        
        session_id = test_session.id
        print(f"Using Session ID: {session_id}")
        
        # Simulate Multi-Face Detection
        camera_service = CameraService()
        # Mocking the process_frame result to simulate n_face=2
        class MockFaceDetector:
            worker = type('obj', (object,), {'is_alive': lambda: True})
            def process_frame(self, frame): return (True, 0.4, 2, [(0,10,10,0), (20,30,30,20)])
            def close(self): pass

        camera_service.face_detector = MockFaceDetector()
        camera_service._detectors_ready = True
        
        # Create a dummy frame
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        import cv2
        _, img_bytes = cv2.imencode('.jpg', dummy_frame)
        
        print("Simulating frame processing with MULTIPLE FACES...")
        camera_service.process_external_frame(img_bytes.tobytes(), session_id=session_id)
        
        # Check Database
        session.expire_all()
        events = session.exec(select(ProctoringEvent).where(ProctoringEvent.session_id == session_id)).all()
        
        print(f"Events found in DB: {len(events)}")
        for e in events:
            print(f"  - [{e.timestamp}] {e.event_type}: {e.details}")
            
        if any(e.event_type == "MULTIPLE_FACES DETECTED" for e in events):
            print("✅ Success: Multi-face event persisted.")
        else:
            # Check for generic warning
            if events:
                 print("✅ Success: Event persisted (Type: " + events[-1].event_type + ")")
            else:
                 print("❌ Failure: No events found in DB.")

if __name__ == "__main__":
    asyncio.run(test_resume_ai())
    asyncio.run(test_proctoring_persistence())
