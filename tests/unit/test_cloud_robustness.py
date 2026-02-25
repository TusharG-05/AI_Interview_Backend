import pytest
import os
from unittest.mock import MagicMock, patch
import numpy as np
from app.services.audio import AudioService
from app.services.face import FaceRecognizer
from app.services.interview import evaluate_answer_content

@pytest.fixture
def dummy_wav(tmp_path):
    path = tmp_path / "test.wav"
    path.write_bytes(b"dummy audio data")
    return str(path)

@patch("app.services.audio.os.getenv")
@patch("app.services.audio.get_modal_transcribe")
def test_audio_service_modal_fallback_to_hf(mock_get_modal, mock_getenv, dummy_wav):
    # Setup: Modal enabled but fails
    mock_getenv.side_effect = lambda k, default=None: {
        "USE_MODAL": "true",
        "HF_TOKEN": "valid_token",
        "SPACE_ID": "test_space"
    }.get(k, default)
    
    # Mock Modal to fail
    mock_modal_cls = MagicMock()
    mock_get_modal.return_value = mock_modal_cls
    mock_modal_cls().transcribe.remote.side_effect = Exception("Modal Timeout")
    
    with patch("huggingface_hub.InferenceClient") as mock_hf_client:
        mock_hf_instance = mock_hf_client.return_value
        mock_hf_instance.automatic_speech_recognition.return_value = {"text": "HF Fallback Text"}
        
        service = AudioService()
        result = asyncio_run(service.speech_to_text(dummy_wav))
        
        assert "HF Fallback Text" in result
        mock_hf_instance.automatic_speech_recognition.assert_called_once()

@patch("app.services.audio.os.getenv")
def test_audio_service_skips_local_on_cloud(mock_getenv, dummy_wav):
    # Setup: Modal disabled, HF disabled, on Spaces
    mock_getenv.side_effect = lambda k, default=None: {
        "USE_MODAL": "false",
        "HF_TOKEN": None,
        "SPACE_ID": "test_space"
    }.get(k, default)
    
    service = AudioService()
    result = asyncio_run(service.speech_to_text(dummy_wav))
    
    assert "[STT Error: Cloud Environment detected. Skipping heavy local STT fallback.]" == result

@patch("app.services.face.os.getenv")
def test_face_recognizer_builds_sface_even_on_cloud(mock_getenv):
    mock_getenv.side_effect = lambda k, default=None: {
        "SPACE_ID": "test_space"
    }.get(k, default)
    
    with patch("deepface.DeepFace.build_model") as mock_build:
        recognizer = FaceRecognizer()
        mock_build.assert_called_once_with("SFace")

@patch("app.services.interview.os.getenv")
@patch("app.services.interview.InferenceClient")
def test_llm_fallback_to_hf(mock_hf_client, mock_getenv):
    mock_getenv.side_effect = lambda k, default=None: {
        "USE_MODAL": "false",
        "HF_TOKEN": "valid_token"
    }.get(k, default)
    
    mock_hf_instance = mock_hf_client.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"feedback": "HF LLM Feedback", "score": 8.5}'
    mock_hf_instance.chat_completion.return_value = mock_response
    
    result = evaluate_answer_content("Question?", "Answer")
    assert result["feedback"] == "HF LLM Feedback"
    assert result["score"] == 8.5

def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)
