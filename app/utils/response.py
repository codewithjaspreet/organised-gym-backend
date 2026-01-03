from typing import Optional, TypeVar, Any
from fastapi import status
from fastapi.responses import JSONResponse
from app.schemas.response import APIResponse

T = TypeVar('T')


def success_response(
    data: Optional[T] = None,
    message: str = "Operation completed successfully"
) -> APIResponse[T]:
    """
    Create a successful API response
    
    Args:
        data: The response data (optional)
        message: Success message
    
    Returns:
        APIResponse with status=True
    """
    return APIResponse(
        status=True,
        message=message,
        data=data
    )


def failure_response(
    message: str = "Operation failed",
    data: Optional[Any] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    Create a failed API response with proper HTTP status code
    
    Args:
        message: Error message
        data: Optional error details
        status_code: HTTP status code (default: 400)
    
    Returns:
        JSONResponse with status=False and appropriate HTTP status code
    """
    return JSONResponse(
        status_code=status_code,
        content=APIResponse(
            status=False,
            message=message,
            data=data
        ).model_dump()
    )

