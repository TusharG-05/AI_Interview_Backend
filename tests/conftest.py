
import os
import sys
import pytest
from unittest.mock import MagicMock

# --- 1. MOCK HEAVY LIBRARIES BEFORE APP IMPORT ---
# We inject these mocks into sys.modules so the app uses them immediately.

sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torchaudio"] = MagicMock()
sys.modules["tensorflow"] = MagicMock()
sys.modules["tf_keras"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["speechbrain"] = MagicMock()
sys.modules["speechbrain.pretrained"] = MagicMock()
sys.modules["speechbrain.inference"] = MagicMock()
sys.modules["speechbrain.inference.speaker"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["deepface"] = MagicMock()
sys.modules["mediapipe"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["langchain_ollama"] = MagicMock()

# Mock audio processing dependencies
sys.modules["edge_tts"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["resampy"] = MagicMock()
# NOTE: Do NOT mock numpy - it's a core dependency used by pydantic/sqlmodel

# Mock Pydub to avoid ffmpeg dependency in tests
pydub = MagicMock()
pydub.AudioSegment = MagicMock()
sys.modules["pydub"] = pydub

# Mock internal service modules that rely on hardware/heavy libs
sys.modules["app.services.camera"] = MagicMock()
sys.modules["app.services.webrtc"] = MagicMock()

# Mock External APIs (Modal, HF)
sys.modules["modal"] = MagicMock()
sys.modules["huggingface_hub"] = MagicMock()

# --- 2. DB MOCKS & FIXTURES ---
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

@pytest.fixture(name="session", scope="function")
def mock_db_session():
    """
    Creates an in-memory SQLite database for the session.
    """
    from app.models.db_models import User, UserRole
    from app.auth.security import get_password_hash

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Enable SQLite foreign key enforcement
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="test_users", scope="function")
def test_users_fixture(session):
    """
    Creates a test admin and candidate user and returns (admin, candidate).
    Use their .id values when creating InterviewSession objects in tests.
    """
    from app.models.db_models import User, UserRole
    from app.auth.security import get_password_hash

    admin = User(
        email="test_admin@example.com",
        full_name="Test Admin",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.ADMIN,
    )
    candidate = User(
        email="test_candidate@example.com",
        full_name="Test Candidate",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.CANDIDATE,
    )
    session.add(admin)
    session.add(candidate)
    session.commit()
    session.refresh(admin)
    session.refresh(candidate)
    return admin, candidate

@pytest.fixture(autouse=True)
def override_dependencies(session):
    """
    Override get_db and init_db to prevent real DB connections.
    """
    # 1. Mock the init_db call to avoid engine creation
    try:
        import app.core.database
        app.core.database.init_db = MagicMock()
    except ImportError:
        pass
    
    # 2. Override the get_db dependency
    from app.core.database import get_db
    from app.server import app
    
    def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(name="client")
def client_fixture(session):
    """
    TestClient fixture for FastAPI apps.
    Overrides the get_db dependency per test function.
    """
    from app.server import app
    from app.core.database import get_db
    
    def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    
    from fastapi.testclient import TestClient
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for each test case.
    """
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def auth_headers(client):
    """
    Creates a test user and returns JWT headers.
    """
    # Create test user
    from app.models.db_models import User, UserRole
    from app.auth.security import create_access_token
    
    # We can invoke the registration endpoint or just mock the token
    # For speed, we'll mock the token generation directly
    access_token = create_access_token(data={"sub": "test@example.com"})
    return {"Authorization": f"Bearer {access_token}"}

