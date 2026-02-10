"""
Response Helper Utilities

Provides convenience functions for creating standardized API responses.
"""

from typing import TypeVar
from app.schemas.api_response import ApiResponse

T = TypeVar('T')


def success_response(
    data: T, 
    message: str = "Success", 
    status_code: int = 200
) -> ApiResponse[T]:
    """
    Create a successful API response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        ApiResponse with status_code, data, and message
    """
    return ApiResponse(
        status_code=status_code,
        data=data,
        message=message
    )
