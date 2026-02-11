import json
from typing import TypeVar, Callable, Any
from fastapi import Response
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from app.schemas.api_response import ApiResponse

T = TypeVar('T')


def success_response(
    data: T, 
    message: str = "Success", 
    status_code: int = 200
) -> ApiResponse[T]:
    """Manually create a successful API response."""
    return ApiResponse(
        status_code=status_code,
        data=data,
        message=message
    )


class StandardizedRoute(APIRoute):
    """
    Custom APIRoute that wraps all responses in a standardized format.
    Excludes the /token endpoint for OAuth2 compatibility.
    """
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def standardized_handler(request) -> Response:
            response = await original_route_handler(request)
            
            # 1. Skip for OAuth2 token path
            if request.url.path.endswith("/token"):
                return response
            
            # 2. Skip File and Streaming responses
            if isinstance(response, (FileResponse, StreamingResponse)):
                return response
            
            # 3. Handle JSONResponse or dict/model returns
            if isinstance(response, JSONResponse):
                try:
                    # Parse current content
                    # body is bytes, need to decode
                    body_content = json.loads(response.body.decode())
                    
                    # Avoid double wrapping
                    if isinstance(body_content, dict) and "status_code" in body_content and "data" in body_content:
                        return response

                    # Wrap content
                    wrapped = ApiResponse(
                        status_code=response.status_code,
                        data=body_content,
                        message="Success"
                    )
                    return JSONResponse(
                        status_code=response.status_code,
                        content=wrapped.model_dump(),
                        headers=dict(response.headers)
                    )
                except Exception:
                    # If not JSON or error parsing, return as is
                    return response

            # 4. If it's another type of response, return as is (e.g. plain text)
            return response

        return standardized_handler
