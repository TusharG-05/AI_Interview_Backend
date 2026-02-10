
import pytest
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash

@pytest.fixture
def admin_user(session):
    user = User(
        email="admin@test.com",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        full_name="Super Admin",
        password_hash=get_password_hash("adminpass")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def test_get_users_as_admin(client, session, admin_user):
    from app.routers.admin import get_admin_user
    from app.server import app

    app.dependency_overrides[get_admin_user] = lambda: admin_user
    
    response = client.get("/api/admin/users")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["email"] == "admin@test.com"
    
    app.dependency_overrides.pop(get_admin_user)

def test_get_users_unauthorized(client):
    response = client.get("/api/admin/users")
    assert response.status_code in [401, 403]
