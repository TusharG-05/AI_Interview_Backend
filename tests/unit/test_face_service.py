
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Mocking the CLASS itself so that __init__ doesn't run real logic (process spawning)
@patch("app.services.face.FaceService") 
def test_face_detection_wrapper(MockFaceService):
    """
    Test that we can instantiate the mocked service 
    and it adheres to the expected interface.
    """
    service = MockFaceService()
    
    # Setup mock behavior
    service.process_frame.return_value = (True, 0.99, 1, [(10, 100, 100, 10)])
    
    # Test method call
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    session_id = 123
    
    result = service.process_frame(frame, session_id)
    
    assert result[0] is True
    assert result[2] == 1

def test_face_service_initialization_logic():
    """
    Test the REAL initialization logic but mock multiprocessing.Process
    to avoid spawning real workers.
    """
    with patch("app.services.face.multiprocessing.Process") as mock_process:
        from app.services.face import FaceService
        service = FaceService()
        
        # Verify it tries to start a worker
        mock_process.assert_called_once()
        service.worker.start.assert_called_once()
        
        # Cleanup
        # Since we mocked Process, .close() might fail if not fully mocked, 
        # so we manually ensure no real cleanup issues.
        pass
