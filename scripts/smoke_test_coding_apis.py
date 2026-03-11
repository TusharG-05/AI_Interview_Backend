"""
Smoke test for all modified modules in the coding question API update.
Run from project root: .venv\Scripts\python.exe -m scripts.smoke_test_coding_apis
"""
import sys, os

errors = []

def check(label, fn):
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)

# 1. Requests schema
check("GenerateCodingPaperRequest.coding_paper_id exists", lambda: (
    __import__("app.schemas.requests", fromlist=["GenerateCodingPaperRequest"]).GenerateCodingPaperRequest
    .__fields__["coding_paper_id"]
))

# 2. CodingPaperFull, CodingQuestionFull importable from responses
check("CodingPaperFull / CodingQuestionFull importable", lambda: (
    __import__("app.schemas.responses", fromlist=["CodingPaperFull", "CodingQuestionFull"]),
))

# 3. CodingQuestions importable from db_models
check("CodingQuestions importable from db_models", lambda: (
    __import__("app.models.db_models", fromlist=["CodingQuestions"]).CodingQuestions
))

# 4. QuestionData has coding_content field
def _check_question_data():
    QD = __import__("app.schemas.interview_responses", fromlist=["QuestionData"]).QuestionData
    assert "coding_content" in QD.model_fields, "missing coding_content field"
check("QuestionData.coding_content field present", _check_question_data)

# 5. QuestionData auto-populates coding_content for code-type questions
def _check_coding_content_auto():
    import json
    QD = __import__("app.schemas.interview_responses", fromlist=["QuestionData"]).QuestionData
    payload = json.dumps({"title": "Two Sum", "problem_statement": "...", "examples": [], "constraints": [], "starter_code": ""})
    q = QD(id=1, paper_id=1, content=payload, question_text="__coding__1",
            topic="Arrays", difficulty="Easy", marks=5, response_type="code")
    assert q.coding_content is not None, "coding_content should be auto-populated"
    assert q.coding_content["title"] == "Two Sum"
check("QuestionData auto-populates coding_content", _check_coding_content_auto)

# 6. coding_papers router importable
check("coding_papers.router importable", lambda: (
    __import__("app.routers.coding_papers", fromlist=["router"]).router
))

# 7. InterviewScheduleCreate validator (both optional + at_least_one)
def _check_validator():
    from pydantic import ValidationError
    SC = __import__("app.schemas.requests", fromlist=["InterviewScheduleCreate"]).InterviewScheduleCreate
    # coding only
    SC(candidate_id=1, coding_paper_id=5, team_id=1, interview_round="ROUND_1", schedule_time="2026-01-01T00:00:00Z")
    # both provided
    SC(candidate_id=1, paper_id=3, coding_paper_id=5, team_id=1, interview_round="ROUND_1", schedule_time="2026-01-01T00:00:00Z")
    # neither — must raise
    try:
        SC(candidate_id=1, team_id=1, interview_round="ROUND_1", schedule_time="2026-01-01T00:00:00Z")
        raise AssertionError("Should have raised")
    except ValidationError:
        pass
check("InterviewScheduleCreate validator OK", _check_validator)

print()
if errors:
    print(f"FAILED: {len(errors)} check(s) failed: {errors}")
    sys.exit(1)
else:
    print(f"All {7} checks passed.")
