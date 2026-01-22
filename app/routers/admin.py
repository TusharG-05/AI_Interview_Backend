from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db, Question, init_db
from ..services.nlp import NLPService
import os
import shutil

router = APIRouter(prefix="/admin", tags=["admin"])
nlp_service = NLPService()

# Initialize DB on first load of admin (or we could do it in lifespan)
init_db()

@router.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()

@router.post("/upload-doc")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file temporarily
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = f"temp_uploads/{file.filename}"
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
