
import unittest

def calculate_scaled_score(llm_score, question_marks):
    """(Isolated copy for testing) Scale a 0-10 LLM score to the question's marks."""
    try:
        llm_score = float(llm_score)
    except (ValueError, TypeError):
        llm_score = 0.0
    
    scaling_factor = float(question_marks) / 10.0
    final_score = llm_score * scaling_factor
    
    # Safeguards: Clamp to [0, marks] and round to 1 decimal place
    final_score_float = float(final_score)
    final_score_clamped = max(0.0, min(final_score_float, float(question_marks)))
    return round(final_score_clamped, 1)

class TestScoringLogic(unittest.TestCase):
    def test_standard_scaling(self):
        self.assertEqual(calculate_scaled_score(10, 5), 5.0)
        self.assertEqual(calculate_scaled_score(5, 5), 2.5)
        self.assertEqual(calculate_scaled_score(0, 5), 0.0)
        self.assertEqual(calculate_scaled_score(8, 20), 16.0)
        
    def test_rounding(self):
        # 7.7/10 of 3 marks = 2.31 -> 2.3
        self.assertEqual(calculate_scaled_score(7.7, 3), 2.3)
        # 3.3/10 of 5 marks = 1.65 -> 1.6 or 1.7 (depending on round strategy) 
        # Actually 1.65 rounds to 1.6 in Python 3 (round to nearest even)
        # 1.66 -> 1.7
        self.assertEqual(calculate_scaled_score(3.32, 5), round(1.66, 1))

    def test_clamping(self):
        self.assertEqual(calculate_scaled_score(11, 10), 10.0)
        self.assertEqual(calculate_scaled_score(-1, 10), 0.0)

    def test_precision(self):
        # 1/3 of 10 marks -> 3.3333 -> 3.3
        self.assertEqual(calculate_scaled_score(3.3333333, 10), 3.3)

if __name__ == '__main__':
    unittest.main()
