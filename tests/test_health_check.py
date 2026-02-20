import pytest
from app.core.config import APP_TITLE

def test_app_title():
    """Verify that we can import from app and config is loaded"""
    assert APP_TITLE == "Face/Gaze Aware AI Interview Platform"

def test_root_endpoint(client):
    """Verify the API is reachable via TestClient"""
    response = client.get("/")
    # Depending on your root route, this might be 200 or 404 if not defined
    # Let's assume there's a root or docs
    # If root is not defined, let's check docs
    if response.status_code == 404:
        response = client.get("/docs")
    
    assert response.status_code == 200

def test_database_fixture(session):
    """Verify the database session fixture works"""
    from sqlalchemy import text
    result = session.exec(text("SELECT 1")).first()
    assert result == (1,)
