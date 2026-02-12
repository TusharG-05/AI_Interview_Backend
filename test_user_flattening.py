"""
Test to verify serialize_user returns flat dictionaries
"""
from app.schemas.user_schemas import serialize_user
from app.models.db_models import User, UserRole

# Test 1: Serialize a regular user
test_user = User(
    id=1,
    email="test@example.com",
    full_name="Test User",
    password_hash="hashed",
    role=UserRole.CANDIDATE
)

result = serialize_user(test_user)
print("Test 1 - Regular User:")
print(f"  Result: {result}")
print(f"  Has 'candidate' key: {'candidate' in result}")
print(f"  Has 'id' key: {'id' in result}")
print(f"  Expected: Flat dict with id, email, full_name, role")
assert 'id' in result, "Should have 'id' at top level"
assert 'candidate' not in result, "Should NOT have 'candidate' wrapper key"
assert result['id'] == 1
assert result['email'] == "test@example.com"
print("  PASSED!\n")

# Test 2: Serialize deleted user (None)
result_deleted = serialize_user(None, fallback_name="Deleted Candidate", fallback_role="candidate")
print("Test 2 - Deleted User:")
print(f"  Result: {result_deleted}")
print(f"  Has 'candidate' key: {'candidate' in result_deleted}")
print(f"  Has 'id' key: {'id' in result_deleted}")
assert result_deleted['id'] is None
assert result_deleted['full_name'] == "Deleted Candidate"
assert 'candidate' not in result_deleted, "Should NOT have 'candidate' wrapper key"
print("  PASSED!\n")

print("=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
print("\nUser response structure is now flat:")
print("  Before: {'candidate': {'id': 1, 'email': '...'}}")
print("  After:  {'id': 1, 'email': '...'}")
