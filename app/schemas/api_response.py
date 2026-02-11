"""
Standardized API Response Models

Provides consistent response format across all endpoints.
"""

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for successful requests
    
    Example:
        {
            "status_code": 200,
            "data": { ... },
            "message": "Success"
        }
    """
    status_code: int = Field(default=200)
    data: T
    message: str = Field(default="Success")


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
    data: Optional[Any] = Field(default=None)
    message: str = Field(default="Error")
