"""
Quick test to verify success field auto-derivation works correctly
"""
from app.schemas.api_response import ApiResponse, ApiErrorResponse

# Test 1: Success response (status_code 200)
success_response = ApiResponse(
    status_code=200,
    data={"user": "test"},
    message="Success"
)
print("Test 1 - Success Response (200):")
print(f"  status_code: {success_response.status_code}")
print(f"  success: {success_response.success}")
print(f"  Expected: True, Got: {success_response.success}")
assert success_response.success == True, "Failed: 200 should have success=True"
print("  PASSED\n")

# Test 2: Error response (status_code 401)
error_response = ApiErrorResponse(
    status_code=401,
    message="Unauthorized"
)
print("Test 2 - Error Response (401):")
print(f"  status_code: {error_response.status_code}")
print(f"  success: {error_response.success}")
print(f"  Expected: False, Got: {error_response.success}")
assert error_response.success == False, "Failed: 401 should have success=False"
print("  PASSED\n")

# Test 3: Created response (status_code 201)
created_response = ApiResponse(
    status_code=201,
    data={"id": 123},
    message="Created"
)
print("Test 3 - Created Response (201):")
print(f"  status_code: {created_response.status_code}")
print(f"  success: {created_response.success}")
print(f"  Expected: True, Got: {created_response.success}")
assert created_response.success == True, "Failed: 201 should have success=True"
print("  PASSED\n")

# Test 4: Server Error (status_code 500)
server_error = ApiErrorResponse(
    status_code=500,
    message="Internal Server Error"
)
print("Test 4 - Server Error (500):")
print(f"  status_code: {server_error.status_code}")
print(f"  success: {server_error.success}")
print(f"  Expected: False, Got: {server_error.success}")
assert server_error.success == False, "Failed: 500 should have success=False"
print("  PASSED\n")

# Test 5: Check JSON output format
print("Test 5 - JSON Output Format:")
print(success_response.model_dump())
expected_keys = {'status_code', 'data', 'message', 'success'}
actual_keys = set(success_response.model_dump().keys())
assert expected_keys == actual_keys, f"Failed: Expected keys {expected_keys}, got {actual_keys}"
print("  All fields present (status_code, data, message, success)\n")

print("=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
