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
            
            # 1. Skip for OAuth2 token path and non-JSON routes
            if request.url.path.endswith("/token") or "/docs" in request.url.path or "/redoc" in request.url.path:
                return response
            
            # 2. Skip File and Streaming responses
            if isinstance(response, (FileResponse, StreamingResponse)):
                return response
            
            # 3. Handle JSON-like responses
            if isinstance(response, JSONResponse) or "application/json" in response.headers.get("content-type", ""):
                try:
                    # Parse current content
                    body = response.body.decode()
                    if not body:
                        return response
                        
                    body_content = json.loads(body)
                    
                    # Avoid double wrapping
                    if isinstance(body_content, dict) and "status_code" in body_content and "data" in body_content:
                        return response

                    # Extract custom message if it exists
                    message = "Success" if response.status_code < 400 else "Error"
                    data = body_content
                    
                    if isinstance(body_content, dict):
                        if "message" in body_content:
                            message = body_content.pop("message")
                        
                        # Handle explicitly returned 'data' structure
                        if "data" in body_content and len(body_content) == 1:
                            data = body_content["data"]
                        else:
                            data = body_content

                    wrapped = ApiResponse(
                        status_code=response.status_code,
                        data=data,
                        message=message
                    )
                    
                    # Build new response with recalculated Content-Length
                    headers = dict(response.headers)
                    headers.pop("content-length", None)
                    return JSONResponse(
                        status_code=response.status_code,
                        content=wrapped.model_dump(),
                        headers=headers
                    )
                except Exception:
                    # Fallback to original if parsing fails
                    return response

            return response

        return standardized_handler
