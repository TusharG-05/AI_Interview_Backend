from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    status_code: int = 200
    data: Optional[T] = None
    message: str = "Success"
    success: bool = True

class ApiErrorResponse(BaseModel):
    status_code: int = 400
    message: str = "Error"
    data: Optional[Any] = None
    success: bool = False
