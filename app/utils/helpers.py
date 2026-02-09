"""Utility functions for common operations."""
from typing import List, Optional


def calculate_average_score(scores: List[Optional[float]]) -> float:
    """Calculate average score with safe handling of empty lists and None values.
    
    Args:
        scores: List of scores, may contain None values
        
    Returns:
        Average of non-None scores, or 0.0 if all scores are None or list is empty
    """
    valid_scores = [s for s in scores if s is not None]
    return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
