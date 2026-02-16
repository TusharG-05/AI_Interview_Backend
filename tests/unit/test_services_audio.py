
import pytest
from unittest.mock import MagicMock, patch
from app.services.audio import AudioService

@pytest.fixture
def audio_service():
    """Fixture to initialize AudioService with mocked dependencies."""
    return AudioService()

def test_convert_to_wav_success(audio_service):
    """Test successful conversion logic using mocked AudioSegment."""
    # Patch the AudioSegment that was imported in app.services.audio
    # Since we mocked pydub in conftest, AudioSegment is already a Mock object.
    # We configure that mock instance or patch the name in the module.
    
    with patch("pydub.AudioSegment") as MockAudioSegment:
        # Arrange
        mock_segment = MagicMock()
        MockAudioSegment.from_file.return_value = mock_segment
        mock_segment.export.return_value = None  # simulate successful export
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.set_channels.return_value = mock_segment
        
        # Act
        # The method uses input_path.rsplit(".", 1)[0] + ".wav"
        output_path = audio_service.convert_to_wav("input.webm")
        
        # Assert
        assert output_path == "input.wav"
        MockAudioSegment.from_file.assert_called_with("input.webm")
        # Ensure export was called
        mock_segment.export.assert_called()

def test_calculate_energy(audio_service):
    with patch("pydub.AudioSegment") as MockAudioSegment:
        mock_segment = MagicMock()
        mock_segment.rms = 100
        MockAudioSegment.from_file.return_value = mock_segment
        
        energy = audio_service.calculate_energy("test.wav")
        assert energy == 100

def test_convert_to_wav_failure(audio_service):
    with patch("pydub.AudioSegment") as MockAudioSegment:
        MockAudioSegment.from_file.side_effect = Exception("FFmpeg error")
        
        # The service logs error and returns None, it doesn't raise
        output = audio_service.convert_to_wav("corrupt.file")
        assert output is None
