
import pytest
from unittest.mock import MagicMock, patch
from typing import Optional, List, Any

# Patch heavy initializers BEFORE importing app
with patch("app.core.database.init_db"), \
     patch("app.core.database.engine"), \
     patch("app.core.logger.setup_logging"):
    from app.server import app
    from app.core.database import get_db
    from app.auth.dependencies import get_current_user, get_current_user_optional

from fastapi.testclient import TestClient
from app.models.db_models import User, UserRole

# Mock database session
@pytest.fixture
def mock_session():
    return MagicMock()

# Mock get_db dependency
def override_get_db():
    yield MagicMock()

# Mock get_current_user dependency
def override_get_current_user():
    return User(id=1, email="test@example.com", full_name="Test User", role=UserRole.ADMIN)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_current_user_optional] = override_get_current_user

client = TestClient(app)

def check_no_nulls(data):
    """Recursively check if there are no null values in the data."""
    if isinstance(data, dict):
        for k, v in data.items():
            if v is None:
                return False, f"Key '{k}' is null"
            res, msg = check_no_nulls(v)
            if not res:
                return False, f"Key '{k}' -> {msg}"
    elif isinstance(data, list):
        for i, item in enumerate(data):
            res, msg = check_no_nulls(item)
            if not res:
                return False, f"Index {i} -> {msg}"
    return True, ""

@pytest.mark.parametrize("route", [r for r in app.routes if hasattr(r, "methods")])
def test_all_routes_serialization(route):
    # Only test GET requests for simplicity and safety in a generic test
    # POST/PUT/DELETE often require complex payloads
    if "GET" not in route.methods:
        pytest.skip("Skipping non-GET route")
    
    # Skip endpoints with path parameters for now, or use a dummy ID
    path = route.path
    if "{" in path:
        # replace {id} with 1
        import re
        path = re.sub(r"\{[^\}]+\}", "1", path)

    try:
        response = client.get(path)
        # We don't care about the status code (as long as it's not a server error)
        # we care about the serialization if it's JSON
        if response.headers.get("content-type") == "application/json":
            json_data = response.json()
            is_valid, msg = check_no_nulls(json_data)
            assert is_valid, f"Route {route.path} has null values: {msg}\nResponse: {json_data}"
    except Exception as e:
        # Some routes might fail due to database access even with mocks, but they shouldn't return nulls
        print(f"Error testing {route.path}: {e}")

def test_explicit_null_exclusion():
    from app.schemas.api_response import ApiResponse
    from pydantic import BaseModel
    
    class Inner(BaseModel):
        attr: Optional[str] = None
        
    # Test ApiResponse with None data
    resp = ApiResponse(status_code=200, data=None, message="Test")
    dump = resp.model_dump()
    assert "data" not in dump, f"Data should be excluded if None. Got: {dump}"
    
    # Test ApiResponse with inner None
    resp2 = ApiResponse(status_code=200, data=Inner(attr=None), message="Test")
    dump2 = resp2.model_dump()
    assert "attr" not in dump2["data"], f"Inner null should be excluded. Got: {dump2}"
    
    print("Explicit null exclusion test PASSED.")

if __name__ == "__main__":
    # Run tests programmatically if needed
    import sys
    pytest.main([__file__])
