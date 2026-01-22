from sqlmodel import SQLModel
from models.db_models import User, InterviewRoom, InterviewSession, Question, InterviewResponse

print("Imported models successfully.")

try:
    User.model_rebuild()
    InterviewRoom.model_rebuild()
    InterviewSession.model_rebuild()
    Question.model_rebuild()
    InterviewResponse.model_rebuild()
    print("Rebuilt models successfully.")
except Exception as e:
    print(f"Error rebuilding models: {e}")
