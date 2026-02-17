import pytest
from unittest.mock import MagicMock, patch
import os

def test_modal_evaluator_success():
    """Test that Modal is used when available"""
    with patch("app.services.interview.USE_MODAL", True):
        with patch("app.services.interview.get_modal_evaluator") as mock_get_eval:
            # Mock the Modal Class and its method
            mock_cls = MagicMock()
            mock_instance = MagicMock()
            mock_remote = MagicMock(return_value={"feedback": "Modal feedback", "score": 9.0})
            
            mock_instance.evaluate.remote = mock_remote
            mock_cls.return_value = mock_instance
            mock_get_eval.return_value = mock_cls
            
            from app.services.interview import evaluate_answer_content
            result = evaluate_answer_content("Q", "A")
            
            assert result["score"] == 9.0
            assert result["feedback"] == "Modal feedback"
            mock_remote.assert_called_once()

def test_modal_failure_hf_fallback():
    """Test fallback to HF when Modal fails"""
    with patch("app.services.interview.USE_MODAL", True):
        # 1. Mock Modal to FAIL
        with patch("app.services.interview.get_modal_evaluator") as mock_get_eval:
            mock_cls = MagicMock()
            mock_instance = MagicMock()
            # Simulate remote call failing
            mock_instance.evaluate.remote.side_effect = Exception("Modal Timeout")
            mock_cls.return_value = mock_instance
            mock_get_eval.return_value = mock_cls
            
            # 2. Mock HF Client to SUCCEED
            with patch("app.services.interview.InferenceClient") as mock_hf_client:
                mock_client_instance = MagicMock()
                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content='{"feedback": "HF feedback", "score": 8.0}'))]
                mock_client_instance.chat_completion.return_value = mock_response
                mock_hf_client.return_value = mock_client_instance
                
                # Ensure HF_TOKEN is present
                with patch.dict(os.environ, {"HF_TOKEN": "valid_token"}):
                    from app.services.interview import evaluate_answer_content
                    result = evaluate_answer_content("Q", "A")
                    
                    assert result["score"] == 8.0
                    assert result["feedback"] == "HF feedback"
                    
                    # Verify both were called
                    mock_instance.evaluate.remote.assert_called_once()
                    mock_client_instance.chat_completion.assert_called_once()

def test_all_services_failure_ollama_fallback():
    """Test fallback to Ollama (local) if both Modal and HF fail"""
    with patch("app.services.interview.USE_MODAL", True):
        # 1. Mock Modal FAIL
        with patch("app.services.interview.get_modal_evaluator", return_value=None):
            # 2. Mock HF FAIL
             with patch("app.services.interview.InferenceClient", side_effect=Exception("HF Error")):
                 with patch.dict(os.environ, {"HF_TOKEN": "valid_token"}):
                     # 3. Mock Local Chain (Ollama)
                     with patch("app.services.interview.evaluation_chain") as mock_chain:
                         mock_chain.invoke.return_value = MagicMock(content='{"feedback": "Local feedback", "score": 7.0}')
                         
                         from app.services.interview import evaluate_answer_content
                         result = evaluate_answer_content("Q", "A")
                         
                         assert result["score"] == 7.0
                         assert result["feedback"] == "Local feedback"
