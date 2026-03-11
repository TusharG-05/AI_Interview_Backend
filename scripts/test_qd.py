from app.schemas.interview_responses import QuestionData

def test_question_data_validator():
    import json
    content = json.dumps({"title": "Test Problem", "problem_statement": "Do something", "examples": []})
    q = QuestionData(
        id=1, paper_id=1, content=content, question_text="Test Problem",
        topic="Testing", difficulty="easy", marks=10, response_type="code"
    )
    print(q.model_dump())
    assert q.coding_content is not None
    assert q.coding_content["title"] == "Test Problem"
    print("Validator works.")

if __name__ == "__main__":
    test_question_data_validator()
