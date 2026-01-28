from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.db_models import Question, InterviewSession, InterviewResponse as CandidateResponse
import os
from datetime import datetime
import uuid
from ..services.audio import AudioService
from ..services.nlp import NLPService
from pydantic import BaseModel

class TTSRange(BaseModel):
    text: str

class EvaluateRequest(BaseModel):
    candidate_text: str
    reference_text: str

router = APIRouter(prefix="/interview", tags=["interview"])
audio_service = AudioService()
nlp_service = NLPService()

@router.post("/start")
async def start_interview(
    candidate_name: str = Form("Candidate"), 
    enrollment_audio: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    session = InterviewSession(candidate_name=candidate_name, start_time=datetime.utcnow())
    db.add(session)
    db.commit()
    db.refresh(session)
    
    warning = None
    if enrollment_audio:
        os.makedirs("app/assets/audio/enrollment", exist_ok=True)
        enrollment_path = f"app/assets/audio/enrollment/enroll_{session.id}.wav"
        content = await enrollment_audio.read()
        audio_service.save_audio_blob(content, enrollment_path)
        
        # Cleanup enrollment audio immediately for better baseline
        audio_service.cleanup_audio(enrollment_path)
        
        # Senior Dev UX: Silence Check
        energy = audio_service.calculate_energy(enrollment_path)
        print(f"DEBUG: Enrollment Energy: {energy}")
        if energy < 50: # RMS Threshold for silence
             warning = "Enrolled audio is very quiet. Speaker verification might be inaccurate."
        
        session.enrollment_audio_path = enrollment_path
        db.commit()
        
    return {"session_id": session.id, "warning": warning}

@router.get("/next-question/{session_id}")
async def get_next_question(session_id: int, db: Session = Depends(get_db)):
    # Simple logic: get the first question that hasn't been answered in this session
    answered_ids = [r.question_id for r in db.query(CandidateResponse).filter(CandidateResponse.session_id == session_id).all()]
    question = db.query(Question).filter(~Question.id.in_(answered_ids)).first()
    
    if not question:
        return {"status": "finished"}
    
    # Generate TTS for the question
    os.makedirs("app/assets/audio/questions", exist_ok=True)
    audio_path = f"app/assets/audio/questions/q_{question.id}.mp3"
    
    # Generate TTS if it doesn't exist
    if not os.path.exists(audio_path):
        await audio_service.text_to_speech(question.question_text, audio_path)
    
    return {
        "question_id": question.id,
        "text": question.question_text,
        "audio_url": f"/interview/audio/question/{question.id}"
    }

@router.get("/audio/question/{q_id}")
async def stream_question_audio(q_id: int):
    audio_path = f"app/assets/audio/questions/q_{q_id}.mp3"
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(audio_path, media_type="audio/mpeg")

@router.post("/submit-answer")
async def submit_answer(
    session_id: int = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs("app/assets/audio/responses", exist_ok=True)
    audio_filename = f"resp_{session_id}_{question_id}_{uuid.uuid4().hex[:8]}.wav"
    audio_path = f"app/assets/audio/responses/{audio_filename}"
    
    # Save the audio blob
    content = await audio.read()
    audio_service.save_audio_blob(content, audio_path)
    
    # Store response (processing is deferred)
    response = CandidateResponse(
        session_id=session_id,
        question_id=question_id,
        audio_path=audio_path
    )
    db.add(response)
    db.commit()
    
    return {"status": "saved"}

@router.post("/finish/{session_id}")
async def finish_interview(session_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.end_time = datetime.utcnow()
    session.is_completed = True
    db.commit()
    
    # Trigger deferred processing in background
    background_tasks.add_task(process_session_results, session_id)
    
    return {"status": "interview_finished", "message": "Results are being processed. Admin can view them later."}

def process_session_results(session_id: int):
    # This runs in background to avoid blocking
    from ..core.database import engine
    from sqlmodel import Session
    with Session(engine) as db:
        try:
            session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            enrollment_path = session.enrollment_audio_path if session else None
            
            responses = db.query(CandidateResponse).filter(CandidateResponse.session_id == session_id).all()
            for i, resp in enumerate(responses):
                try:
                    print(f"DEBUG: Processing Response {i+1}/{len(responses)} (Q_ID: {resp.question_id})...")
                    if resp.audio_path and not resp.transcribed_text:
                        # 0. Cleanup
                        audio_service.cleanup_audio(resp.audio_path)

                        # 1. Speaker Verification (Optional/Fast)
                        if enrollment_path:
                            print(f"DEBUG: Verifying Speaker for Q{resp.question_id}...")
                            is_match, score = audio_service.verify_speaker(enrollment_path, resp.audio_path)
                            if not is_match:
                                resp.transcribed_text = f"[SECURITY ALERT: VOICE MISMATCH ({score:.2f})] "
                            else:
                                resp.transcribed_text = ""
                        
                        # 2. Transcribe (High Speed Tiny Model)
                        print(f"DEBUG: Transcribing Q{resp.question_id} with High-Speed engine...")
                        text = audio_service.speech_to_text(resp.audio_path)
                        print(f"DEBUG: Q{resp.question_id} Result: '{text}'")
                        
                        resp.transcribed_text = (resp.transcribed_text or "") + text
                        
                        # 3. Match with reference
                        q = db.query(Question).filter(Question.id == resp.question_id).first()
                        if q:
                            score = nlp_service.calculate_similarity(text, q.reference_answer)
                            print(f"DEBUG: Q{resp.question_id} Similarity: {score:.2f}")
                            resp.similarity_score = score
                        
                        db.commit() # Save progress instantly
                except Exception as inner_e:
                    print(f"ERROR processing response {resp.id}: {inner_e}")
                    db.rollback()
                    continue

            print(f"DEBUG: Session {session_id} background processing COMPLETED.")
        except Exception as e:
            print(f"CRITICAL Error processing session {session_id}: {e}")



@router.post("/tts")
async def standalone_tts(req: TTSRange):
    """Standalone TTS endpoint for frontend testing."""
    os.makedirs("app/assets/audio/standalone", exist_ok=True)
    temp_id = uuid.uuid4().hex[:8]
    audio_path = f"app/assets/audio/standalone/tts_{temp_id}.mp3"
    
    await audio_service.text_to_speech(req.text, audio_path)
    
    return FileResponse(audio_path, media_type="audio/mpeg")

@router.post("/evaluate")
async def standalone_evaluate(req: EvaluateRequest):
    """Standalone NLP similarity evaluation for frontend testing."""
    score = nlp_service.calculate_similarity(req.candidate_text, req.reference_text)
    return {"score": round(score, 4)}
