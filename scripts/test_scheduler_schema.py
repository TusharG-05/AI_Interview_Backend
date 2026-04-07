from app.schemas.requests import InterviewScheduleCreate
from pydantic import ValidationError

# Test 1: coding_paper_id only (should succeed)
try:
    s = InterviewScheduleCreate(candidate_id=1, coding_paper_id=5, team_id=1, interview_round='ROUND_1', schedule_time='2026-01-01T00:00:00Z')
    assert s.paper_id is None
    assert s.coding_paper_id == 5
    print("Test 1 PASS: coding_paper_id only is valid")
except Exception as e:
    print(f"Test 1 FAIL: {e}")

# Test 2: paper_id only (should succeed)
try:
    s = InterviewScheduleCreate(candidate_id=1, paper_id=3, team_id=1, interview_round='ROUND_1', schedule_time='2026-01-01T00:00:00Z')
    assert s.paper_id == 3
    assert s.coding_paper_id is None
    print("Test 2 PASS: paper_id only is valid")
except Exception as e:
    print(f"Test 2 FAIL: {e}")

# Test 3: both (should succeed)
try:
    s = InterviewScheduleCreate(candidate_id=1, paper_id=3, coding_paper_id=5, team_id=1, interview_round='ROUND_1', schedule_time='2026-01-01T00:00:00Z')
    print("Test 3 PASS: both paper_id and coding_paper_id is valid")
except Exception as e:
    print(f"Test 3 FAIL: {e}")

# Test 4: neither (should fail with validator error)
try:
    s = InterviewScheduleCreate(candidate_id=1, team_id=1, interview_round='ROUND_1', schedule_time='2026-01-01T00:00:00Z')
    print("Test 4 FAIL: should have raised ValidationError")
except ValidationError as e:
    print(f"Test 4 PASS: correctly rejected (neither paper provided): {e.errors()[0]['msg'][:60]}")
except Exception as e:
    print(f"Test 4 PASS (unexpected exception type): {e}")
