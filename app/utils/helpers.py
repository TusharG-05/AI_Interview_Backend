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


def calculate_total_score(scores: List[Optional[float]]) -> float:
    """Calculate cumulative total score (sum) for an interview session.

    Args:
        scores: List of per-answer scores, may contain None values

    Returns:
        Sum of all non-None scores, or 0.0 if list is empty / all None
    """
    return sum(s for s in scores if s is not None)


def calculate_total_marks(session_obj) -> int:
    """Calculate total possible marks from ALL questions in ALL assigned papers.

    Uses the pre-computed ``total_marks`` on each paper when available,
    otherwise falls back to summing individual question marks.

    Args:
        session_obj: An InterviewSession with ``paper`` and ``coding_paper``
                     relationships loaded.

    Returns:
        Total possible marks across all assigned papers, or 0 if none.
    """
    total = 0

    # Standard question paper
    if session_obj.paper:
        paper_marks = session_obj.paper.total_marks
        if paper_marks:
            total += paper_marks
        elif hasattr(session_obj.paper, "questions") and session_obj.paper.questions:
            total += sum(q.marks or 0 for q in session_obj.paper.questions)

    # Coding question paper
    if session_obj.coding_paper:
        coding_marks = session_obj.coding_paper.total_marks
        if coding_marks:
            total += coding_marks
        elif hasattr(session_obj.coding_paper, "questions") and session_obj.coding_paper.questions:
            total += sum(q.marks or 0 for q in session_obj.coding_paper.questions)

    return total


def format_iso_datetime(dt):
    """
    Ensures that ISO strings always include a timezone offset or 'Z' suffix.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat()
