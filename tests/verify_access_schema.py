import sys
sys.path.append(".")
from app.schemas.responses import InterviewAccessResponse
from app.models.db_models import User, QuestionPaper

# Mock data
candidate = User(id=23, email="test@test.com", full_name="Candidate", password_hash="hash")
admin = User(id=1, email="admin@test.com", full_name="Admin", password_hash="hash")
paper = QuestionPaper(id=1, name="Test Paper", admin_id=1)

response = InterviewAccessResponse(
    interview_id=58,
    candidate=candidate.model_dump(),
    admin=admin.model_dump(),
    paper=paper.model_dump(),
    invite_link="http://localhost:3000/interview/token123",
    message="START",
    schedule_time="2026-02-24T18:00:00Z",
    duration_minutes=60,
    status="scheduled",
    max_questions=5
)

# Print as JSON format to verify it matches user requested schema
print(response.model_dump_json(indent=2))
