import pytest
import json
from unittest.mock import patch, MagicMock
from app.models.db_models import CodingQuestionPaper, CodingQuestions, QuestionPaper, Questions, InterviewSession, InterviewStatus, InterviewResult, Answers

def test_coding_paper_auto_creation_and_aggregation(client, session, auth_headers, test_users):
    """
    Test 1: Auto-creation of coding paper (appending is disabled)
    Test 2: Combined score aggregation (Standard + Coding)
    """
    admin, candidate = test_users

    # --- 1. AUTO-CREATION ---
    mock_generated = [
        {"title": "Sum Array", "problem_statement": "Sum it", "marks": 5, "difficulty": "Easy", "topic": "Arrays"},
        {"title": "Max Array", "problem_statement": "Max it", "marks": 5, "difficulty": "Easy", "topic": "Arrays"}
    ]

    with patch("app.services.interview.generate_coding_questions_from_prompt", return_value=mock_generated):
        payload = {
            "ai_prompt": "Basic Array Problems",
            "difficulty_mix": "easy",
            "num_questions": 2,
            "paper_name": "My New Auto Paper"
        }
        # Every request now creates a new paper
        response = client.post("/api/admin/generate-coding-paper", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()["data"]
        new_paper_id = data["id"]
        assert data["name"] == "My New Auto Paper"
        assert len(data["questions"]) == 2

        # Verify in DB
        paper = session.get(CodingQuestionPaper, new_paper_id)
        assert paper is not None
        assert paper.adminUser == admin.id
        assert paper.question_count == 2

    # --- 2. COMBINED SCORE AGGREGATION ---
    # Setup standard paper
    std_paper = QuestionPaper(name="Std Paper", adminUser=admin.id)
    session.add(std_paper)
    session.commit()
    q_std = Questions(paper_id=std_paper.id, content="What is Python?", question_text="What is Python?", marks=5)
    session.add(q_std)
    session.commit()

    # Create interview with BOTH papers
    from datetime import datetime, timezone
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=std_paper.id,
        coding_paper_id=new_paper_id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.LIVE
    )
    session.add(interview)
    session.commit()

    # Create Result and Answers
    result = InterviewResult(interview_id=interview.id)
    session.add(result)
    session.commit()

    # Answer regular question (score 5)
    ans1 = Answers(
        interview_result_id=result.id,
        question_id=q_std.id,
        candidate_answer="A programming language",
        score=5.0,
        feedback="Correct"
    )
    # Answer coding question (score 5)
    # Get the coding question from paper
    cq = session.query(CodingQuestions).filter(CodingQuestions.paper_id == new_paper_id).first()
    ans2 = Answers(
        interview_result_id=result.id,
        coding_question_id=cq.id, 
        candidate_answer="code...",
        score=5.0,
        feedback="Great"
    )
    session.add(ans1)
    session.add(ans2)
    session.commit()

    # Now run background task (synchronously for test)
    from app.tasks.interview_tasks import process_session_results
    process_session_results(interview.id, db=session)

    session.refresh(interview)
    session.refresh(result)
    
    # Total score check: 5 (std) + 5 (coding) = 10
    assert result.total_score == 10.0
    assert result.result_status == "FAIL" 
    assert interview.total_score == 10.0

    # Verify Results API
    response = client.get(f"/api/admin/results/{interview.id}", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert res_data["total_score"] == 10.0
    assert len(res_data["Interview_response"]) == 2
    
    # Check if both types are present
    ans_types = [a.get("question_id") is not None for a in res_data["Interview_response"]]
    assert True in ans_types # Standard
    
    coding_ans = [a.get("coding_question_id") for a in res_data["Interview_response"] if a.get("coding_question_id") is not None]
    assert len(coding_ans) == 1
    assert coding_ans[0]["title"] == "Sum Array"
