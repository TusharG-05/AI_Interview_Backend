"""
Standardized API Response Models

Provides consistent response format across all endpoints.
"""

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for successful requests
    
    Example:
        {
            "status_code": 200,
            "data": {
                "access_token": "...",
                "email": "user@example.com"
            },
            "message": "Login successful"
        }
    """
    status_code: int
    data: T
    message: str


class ApiErrorResponse(BaseModel):
    """
    Standard error response for failed requests
    
    Example:
        {
            "status_code": 401,
            "data": null,
            "message": "Incorrect email or password"
        }
    """
    status_code: int
    data: Optional[Any] = None
    message: str
