"""
Book Schemas - Request/Response DTOs for Book API

Implements Pydantic v2 with validation, Round-trip support, and pagination.
Maps to RULE-009 through RULE-013 business rules.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class BookStatus(str, Enum):
    """Book status values (per RULE-009)"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BookType(str, Enum):
    """Book type values"""
    NORMAL = "normal"
    TEMPLATE = "template"


# ============================================================================
# Request Schemas (Input Validation)
# ============================================================================

class BookCreate(BaseModel):
    """Create Book request (RULE-009: Unlimited creation)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "My First Book",
                "summary": "A collection of notes and ideas",
                "book_type": "normal",
                "priority": 5,
                "urgency": 3,
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    summary: Optional[str] = Field(None, max_length=1000, description="Book summary")
    book_type: BookType = Field(default=BookType.NORMAL, description="Type of book")
    priority: Optional[int] = Field(None, ge=0, le=10, description="Priority level (0-10)")
    urgency: Optional[int] = Field(None, ge=0, le=10, description="Urgency level (0-10)")
    due_at: Optional[datetime] = Field(None, description="Due date for this book")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Strip whitespace and reject empty titles"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip()

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from summary if provided"""
        if v:
            return v.strip()
        return v


class BookUpdate(BaseModel):
    """Update Book request (RULE-009/011)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Updated Title",
                "summary": "Updated summary text",
                "bookshelf_id": "550e8400-e29b-41d4-a716-446655440000",
                "priority": 7,
                "urgency": 5,
            }
        }
    )

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=1000)
    bookshelf_id: Optional[UUID] = Field(None, description="Move to target bookshelf (RULE-011)")
    priority: Optional[int] = Field(None, ge=0, le=10)
    urgency: Optional[int] = Field(None, ge=0, le=10)
    due_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip() if v else None

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v


class BookRestoreRequest(BaseModel):
    """Restore Book from Basement request (RULE-013)"""
    target_bookshelf_id: UUID = Field(..., description="Restore to target bookshelf")


# ============================================================================
# Response Schemas (Output Serialization)
# ============================================================================

class BookDTO(BaseModel):
    """Internal Data Transfer Object (Service → Router layer)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    library_id: UUID
    bookshelf_id: UUID
    title: str
    summary: Optional[str] = None
    book_type: BookType = BookType.NORMAL
    status: BookStatus = BookStatus.DRAFT
    is_pinned: bool = False
    priority: Optional[int] = None
    urgency: Optional[int] = None
    due_at: Optional[datetime] = None
    soft_deleted_at: Optional[datetime] = None
    block_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, book_domain) -> "BookDTO":
        """Convert Book domain object to DTO (RULE-009-013 fields)"""
        return cls(
            id=book_domain.id,
            library_id=book_domain.library_id,
            bookshelf_id=book_domain.bookshelf_id,
            title=book_domain.title.value,  # Value Object
            summary=book_domain.summary.value if book_domain.summary else None,
            book_type=book_domain.book_type,
            status=book_domain.status,
            is_pinned=book_domain.is_pinned,
            priority=book_domain.priority,
            urgency=book_domain.urgency,
            due_at=book_domain.due_at,
            soft_deleted_at=book_domain.soft_deleted_at,
            block_count=book_domain.block_count,
            created_at=book_domain.created_at,
            updated_at=book_domain.updated_at,
        )

    def to_response(self) -> "BookResponse":
        """Convert DTO to API response (standard view)"""
        return BookResponse(
            id=self.id,
            bookshelf_id=self.bookshelf_id,
            title=self.title,
            summary=self.summary,
            book_type=self.book_type,
            status=self.status,
            is_pinned=self.is_pinned,
            priority=self.priority,
            urgency=self.urgency,
            due_at=self.due_at,
            block_count=self.block_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_detail_response(self) -> "BookDetailResponse":
        """Convert DTO to detailed API response (extended view)"""
        return BookDetailResponse(
            id=self.id,
            bookshelf_id=self.bookshelf_id,
            title=self.title,
            summary=self.summary,
            book_type=self.book_type,
            status=self.status,
            is_pinned=self.is_pinned,
            priority=self.priority,
            urgency=self.urgency,
            due_at=self.due_at,
            block_count=self.block_count,
            soft_deleted_at=self.soft_deleted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class BookResponse(BaseModel):
    """Standard Book response (basic fields)"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "bookshelf_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "My First Book",
                "summary": "A collection of notes and ideas",
                "book_type": "normal",
                "status": "draft",
                "is_pinned": False,
                "priority": 5,
                "urgency": 3,
                "due_at": None,
                "block_count": 12,
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    id: UUID
    bookshelf_id: UUID
    title: str
    summary: Optional[str] = None
    book_type: BookType = BookType.NORMAL
    status: BookStatus = BookStatus.DRAFT
    is_pinned: bool
    priority: Optional[int] = None
    urgency: Optional[int] = None
    due_at: Optional[datetime] = None
    block_count: int
    created_at: datetime
    updated_at: datetime


class BookDetailResponse(BookResponse):
    """Extended Book response (with metadata for detail view)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "bookshelf_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "My First Book",
                "summary": "A collection of notes and ideas",
                "book_type": "normal",
                "status": "draft",
                "is_pinned": False,
                "priority": 5,
                "urgency": 3,
                "due_at": None,
                "block_count": 12,
                "soft_deleted_at": None,
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    soft_deleted_at: Optional[datetime] = None  # RULE-012: Soft delete indicator


class BookPaginatedResponse(BaseModel):
    """Paginated Book list response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "page_size": 20,
                "has_more": True,
            }
        }
    )

    items: List[BookDetailResponse]
    total: int = Field(..., ge=0, description="Total number of books")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size (1-100)")
    has_more: bool = Field(..., description="Whether more pages exist")


class BookErrorResponse(BaseModel):
    """Structured error response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "BOOK_NOT_FOUND",
                "message": "Book not found: 550e8400-e29b-41d4-a716-446655440000",
                "details": {
                    "book_id": "550e8400-e29b-41d4-a716-446655440000",
                }
            }
        }
    )

    code: str = Field(..., description="Error code (e.g., BOOK_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error context")
