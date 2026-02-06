
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

@patch("app.services.gaze.GazeDetector")
def test_gaze_detector_mocked(MockGazeDetector):
    """Test interaction with a mocked GazeDetector."""
    service = MockGazeDetector()
    service.process_frame.return_value = "Safe: Center"
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = service.process_frame(frame)
    
    assert result == "Safe: Center"

def test_gaze_initialization_logic():
    """Test real init with mocked multiprocessing."""
    with patch("app.services.gaze.multiprocessing.Process") as mock_process:
        from app.services.gaze import GazeDetector
        
        # Only test init, don't run heavy logic
        service = GazeDetector(model_path="dummy/path", max_faces=1)
        
        mock_process.assert_called_once()
        service.worker.start.assert_called_once()
