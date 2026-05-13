
import unittest
from unittest.mock import MagicMock, patch
import json
from app.services.interview import calculate_scaled_score, evaluate_answer_content

class TestAIReScoring(unittest.TestCase):
    
    def test_calculate_scaled_score(self):
        """Test the pure scaling, clamping and rounding logic."""
        # Standard case: 8/10 on a 5 mark question -> 4.0
        self.assertEqual(calculate_scaled_score(8.0, 5.0), 4.0)
        
        # Rounding case: 7.7/10 on a 3 mark question -> 2.31 -> 2.3
        self.assertEqual(calculate_scaled_score(7.7, 3.0), 2.3)
        
        # Half mark question: 10/10 on a 0.5 mark question -> 0.5
        self.assertEqual(calculate_scaled_score(10.0, 0.5), 0.5)
        
        # Clamping upper: 11/10 on a 10 mark question -> 10.0
        self.assertEqual(calculate_scaled_score(11.0, 10.0), 10.0)
        
        # Clamping lower: -1/10 on a 10 mark question -> 0.0
        self.assertEqual(calculate_scaled_score(-1.0, 10.0), 0.0)
        
        # Invalid input: "bad" as score -> 0.0
        self.assertEqual(calculate_scaled_score("bad", 10.0), 0.0)

    @patch('app.services.interview.get_interview_groq')
    def test_evaluate_answer_scaling_groq(self, mock_get_groq):
        """Test that evaluate_answer_content correctly scales Groq output."""
        mock_groq = MagicMock()
        mock_get_groq.return_value = mock_groq
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "feedback": "Excellent work.",
            "score_out_of_10": 9.5
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Scenario: Question is worth 20 marks
        result = evaluate_answer_content(
            question="Tell me about yourself.",
            answer="I am a software engineer...",
            question_marks=20.0
        )
        # 9.5 out of 10 is 19.0 out of 20
        self.assertEqual(result['score'], 19.0)
        self.assertEqual(result['feedback'], "Excellent work.")

    @patch('app.services.interview.get_interview_groq')
    def test_retry_mechanism(self, mock_get_groq):
        """Test that the 2-attempt retry works if JSON is malformed initially."""
        mock_groq = MagicMock()
        mock_get_groq.return_value = mock_groq
        
        # 1st call fails (malformed JSON), 2nd call succeeds
        mock_groq.chat.completions.create.side_effect = [
            Exception("Simulated API Error"),
            MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({"feedback": "Retry worked", "score_out_of_10": 8.0})))])
        ]

        result = evaluate_answer_content(
            question="Q", answer="A", question_marks=10.0
        )
        self.assertEqual(result['score'], 8.0)
        self.assertEqual(result['feedback'], "Retry worked")
        self.assertEqual(mock_groq.chat.completions.create.call_count, 2)

if __name__ == '__main__':
    unittest.main()
