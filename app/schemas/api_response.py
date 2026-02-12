"""
Standardized API Response Models

Provides consistent response format across all endpoints.
"""

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel
from fastapi.responses import JSONResponse

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for successful requests
    
    The 'success' field is automatically derived from status_code:
    - True if status_code is 2xx (200-299)
    - False otherwise
    
    Example:
        {
            "status_code": 200,
            "data": {
                "access_token": "...",
                "email": "user@example.com"
            },
            "message": "Login successful",
            "success": true
        }
    """
    status_code: int
    data: T
    message: str
    success: bool = True  # Default, will be overridden in __init__
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        # Auto-derive success from status_code if not explicitly provided
        if 'success' not in data:
            status_code = data.get('status_code', 500)
            data['success'] = 200 <= status_code < 300
        super().__init__(**data)


class ApiErrorResponse(BaseModel):
    """
    Standard error response for failed requests
    
    The 'success' field is automatically derived from status_code:
    - True if status_code is 2xx (200-299)
    - False otherwise (typically false for errors)
    
    Example:
        {
            "status_code": 401,
            "data": null,
            "message": "Incorrect email or password",
            "success": false
        }
    """
    status_code: int
    data: Optional[Any] = None
    message: str
    success: bool = False  # Default for errors
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        # Auto-derive success from status_code if not explicitly provided
        if 'success' not in data:
            status_code = data.get('status_code', 500)
            data['success'] = 200 <= status_code < 300
        super().__init__(**data)


def create_response(api_response: ApiResponse | ApiErrorResponse) -> JSONResponse:
    """
    Helper function to create JSONResponse with matching HTTP status code.
    
    Ensures the HTTP response status code matches the body's status_code field.
    
    Args:
        api_response: ApiResponse or ApiErrorResponse instance
        
    Returns:
        JSONResponse with proper HTTP status code
        
    Example:
        return create_response(ApiResponse(
            status_code=200,
            data={"user": "..."},
            message="Success"
        ))
        # Returns HTTP 200 with body containing status_code: 200, success: true
    """
    return JSONResponse(
        status_code=api_response.status_code,
        content=api_response.model_dump()
    )

