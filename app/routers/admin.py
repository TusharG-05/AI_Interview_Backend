from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..core.database import get_db, init_db
from ..models.db_models import Question, InterviewSession, CandidateResponse
from ..services.nlp import NLPService
import os
import shutil
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])
nlp_service = NLPService()

# Initialize DB on first load of admin (or we could do it in lifespan)
init_db()

@router.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()

@router.post("/upload-doc")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file temporarily with unique name
    os.makedirs("temp_uploads", exist_ok=True)
    file_id = uuid.uuid4().hex[:8]
    file_path = f"temp_uploads/{file_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        qa_pairs = nlp_service.extract_qa_from_file(file_path)
        
        # Add to database
        new_questions = []
        for pair in qa_pairs:
            q = Question(
                question_text=pair['question'],
                reference_answer=pair['answer']
            )
            db.add(q)
            new_questions.append(q)
        
        db.commit()
        return {"message": f"Successfully extracted {len(qa_pairs)} questions", "questions": qa_pairs}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.delete("/questions/{q_id}")
def delete_question(q_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}

# --- New Admin Features ---

@router.get("/results")
def get_results(db: Session = Depends(get_db)):
    # Eagerly load all responses and their associated questions to avoid N+1 queries
    sessions = db.query(InterviewSession).options(
        joinedload(InterviewSession.responses).joinedload(CandidateResponse.question)
    ).all()
    
    results = []
    import datetime
    
    for s in sessions:
        responses = s.responses
        # Aggregate score from responses
        valid_scores = [r.similarity_score for r in responses if r.similarity_score is not None]
        avg_score = (sum(valid_scores) / len(responses)) * 100 if responses else 0
        
        flags = [r.transcribed_text for r in responses if "SECURITY ALERT" in (r.transcribed_text or "")]
        
        # Format Timestamp
        formatted_date = s.start_time.strftime("%Y-%m-%d %H:%M")

        # Build Details List
        details = []
        for r in responses:
            q_text = r.question.question_text if r.question else "Unknown Question"
            ans_text = r.transcribed_text or "[No Answer]"
            q_score = f"{round(r.similarity_score * 100, 1)}%" if r.similarity_score is not None else "0%"
            
            details.append({
                "question": q_text,
                "answer": ans_text,
                "score": q_score
            })

        results.append({
            "session_id": s.id,
            "candidate": s.candidate_name,
            "date": formatted_date,
            "score": f"{round(avg_score, 1)}%",
            "status": "Completed" if s.is_completed else "In Progress",
            "flags": len(flags) > 0,
            "details": details
        })
    return results

@router.post("/upload-identity")
async def upload_identity(file: UploadFile = File(...)):
    # Save to known_person.jpg
    content = await file.read()
    
    from ..services.camera import CameraService
    cam = CameraService()
    success = cam.update_identity(content)
    
    if success:
        return {"message": "Identity updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update identity")

@router.post("/shutdown")
def shutdown():
    import os, signal
    os.kill(os.getpid(), signal.SIGTERM)
    return {"message": "Server shutting down..."}
