from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Standardized API response format"""
    status: bool = Field(..., description="Response status: true for success, false for failure")
    message: str = Field(..., description="API message describing the result")
    data: Optional[T] = Field(default=None, description="The actual response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status": True,
                "message": "Data fetched successfully",
                "data": {}
            }
        }

