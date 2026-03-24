from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    status_code: int = 200
    data: Optional[T] = None
    message: str = "Success"
    success: bool = True

    def model_dump(self, **kwargs):
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

class ApiErrorResponse(BaseModel):
    status_code: int = 400
    message: str = "Error"
    data: Optional[Any] = None
    success: bool = False

    def model_dump(self, **kwargs):
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
