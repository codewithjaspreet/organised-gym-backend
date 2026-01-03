from typing import Optional, TypeVar, Any
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
    data: Optional[Any] = None
) -> APIResponse[Any]:
    """
    Create a failed API response
    
    Args:
        message: Error message
        data: Optional error details
    
    Returns:
        APIResponse with status=False
    """
    return APIResponse(
        status=False,
        message=message,
        data=data
    )

