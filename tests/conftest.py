
import os
import sys
import pytest
from unittest.mock import MagicMock

# 1. Mock heavy libraries BEFORE they are imported by the app
#    We use sys.modules to inject mocks so that when the app imports them,
#    requests get the mock object instead of trying to load the actual library.

# Mock Torch
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torchaudio"] = MagicMock()

# Mock TensorFlow
sys.modules["tensorflow"] = MagicMock()
sys.modules["tf_keras"] = MagicMock()

# Mock OpenCV
sys.modules["cv2"] = MagicMock()

# Mock SpeechBrain and Transformers
sys.modules["speechbrain"] = MagicMock()
sys.modules["speechbrain.pretrained"] = MagicMock()
sys.modules["speechbrain.inference"] = MagicMock()
sys.modules["speechbrain.inference.speaker"] = MagicMock()
sys.modules["transformers"] = MagicMock()

# Mock other AI/heavy libs
sys.modules["deepface"] = MagicMock()
sys.modules["mediapipe"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["langchain_ollama"] = MagicMock()

# Mock WebRTC and Camera to prevent side effects in integration tests
sys.modules["aiortc"] = MagicMock()
sys.modules["av"] = MagicMock() # PyAV
sys.modules["app.services.camera"] = MagicMock()
sys.modules["app.services.webrtc"] = MagicMock()

# 2. Setup Database Mock
#    We neeed to mock SQLAlchemy/SQLModel session interactions.

@pytest.fixture(scope="session")
def mock_db_session():
    """Returns a magic mock for the database session."""
    session = MagicMock()
    return session

@pytest.fixture(autouse=True)
def override_get_db(mock_db_session):
    """
    Overrides the dependency injection for get_db.
    This ensures API endpoints use our mock session.
    Also mocks init_db to prevent database connection during startup.
    """
    from app.core.database import get_db
    # Mock init_db to prevent real connection attempt in lifespan
    import app.core.database
    app.core.database.init_db = MagicMock()
    
    from app.server import app
    
    # Define a generator that yields the mock session
    def _get_test_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

# 3. Setup Test Client
#    Using Starlette/FastAPI TestClient.

@pytest.fixture(scope="module")
def client():
    # Ensure init_db is mocked BEFORE importing app.server if possible?
    # Actually, we import app.server here.
    # But override_get_db runs autouse, so it might run before test but AFTER client fixture creation?
    # Wait, client fixture needs 'app'.
    # We should patch init_db globally or before app import.
    
    # Better approach: Patch init_db in sys.modules or override it in app/core/database.py imports?
    # We can rely on the fact that we mocked 'app.core.database' function if we import it first.
    
    # Let's import app.core.database first and patch it
    try:
        import app.core.database
        app.core.database.init_db = MagicMock()
    except ImportError:
        pass

    from app.server import app
    from fastapi.testclient import TestClient
    return TestClient(app)
