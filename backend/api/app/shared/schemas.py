"""
Shared DTOs and response schemas

Provides:
- PageResponse: Generic pagination response wrapper
- ErrorResponse: Standard error response format
- BaseResponse: Generic response envelope
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Any, Optional
from datetime import datetime

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """
    Generic paginated response

    Usage in endpoints:
        return PageResponse[LibraryDTO](
            items=libraries,
            total=100,
            page=1,
            page_size=10,
        )
    """

    items: List[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    has_next: bool
    has_previous: bool
    total_pages: int

    @property
    def pages(self) -> int:
        """Alias for total_pages"""
        return self.total_pages

    class Config:
        arbitrary_types_allowed = True


class ErrorResponse(BaseModel):
    """
    Standard error response format

    Used for both SystemException and BusinessError responses.
    Mapped by exception handlers in main.py
    """

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    details: Optional[dict] = Field(None, description="Additional context")
    trace_id: Optional[str] = Field(None, description="Request ID for debugging")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "LIBRARY_NOT_FOUND",
                "message": "Library '123' not found",
                "timestamp": "2025-11-14T10:30:00Z",
                "details": {"library_id": "123"},
                "trace_id": "req-abc123",
            }
        }


class BaseResponse(BaseModel):
    """
    Base response envelope for API responses

    Can be used to wrap any response data with success status.
    Not always necessary - use directly if status is clear from HTTP code.

    Usage:
        return BaseResponse(
            success=True,
            data={"id": "123", "name": "My Library"},
        )
    """

    success: bool = Field(..., description="Whether operation was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[ErrorResponse] = Field(None, description="Error details if failed")
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "My Library"},
                "timestamp": "2025-11-14T10:30:00Z",
            }
        }
