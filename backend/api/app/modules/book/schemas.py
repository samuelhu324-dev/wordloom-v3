"""
Book Schemas - Request/Response DTOs for Book API

Implements Pydantic v2 with validation, Round-trip support, and pagination.
Maps to RULE-009 through RULE-013 business rules.
"""
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from enum import Enum


COVER_ICON_REGEX = re.compile(r"^[a-z0-9\-]+$")
MAX_COVER_ICON_LENGTH = 64


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


class BookMaturity(str, Enum):
    """Lifecycle stages for Book maturity segmentation"""
    SEED = "seed"
    GROWING = "growing"
    STABLE = "stable"
    LEGACY = "legacy"


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
    cover_icon: Optional[str] = Field(
        default=None,
        max_length=MAX_COVER_ICON_LENGTH,
        description="Lucide icon name (lowercase, hyphen-separated)"
    )
    cover_media_id: Optional[UUID] = Field(
        default=None,
        description="Media UUID for uploaded cover image (null clears)"
    )

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

    @field_validator("cover_icon")
    @classmethod
    def validate_cover_icon(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if len(normalized) > MAX_COVER_ICON_LENGTH:
            raise ValueError(
                f"cover_icon must be <= {MAX_COVER_ICON_LENGTH} characters"
            )
        if not COVER_ICON_REGEX.match(normalized):
            raise ValueError(
                "cover_icon must contain lowercase letters, digits, or '-'"
            )
        return normalized


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
    maturity: Optional[BookMaturity] = Field(
        None,
        description="Set maturity lifecycle (seed → growing → stable → legacy)",
    )
    priority: Optional[int] = Field(None, ge=0, le=10)
    urgency: Optional[int] = Field(None, ge=0, le=10)
    due_at: Optional[datetime] = None
    is_pinned: Optional[bool] = Field(
        None,
        description="Toggle pinned state"
    )
    cover_icon: Optional[str] = Field(
        default=None,
        max_length=MAX_COVER_ICON_LENGTH,
        description="Lucide icon name (lowercase, hyphen-separated)"
    )
    cover_media_id: Optional[UUID] = Field(
        default=None,
        description="Media UUID for uploaded cover image (null clears the custom cover)",
    )
    tag_ids: Optional[List[UUID]] = Field(
        None,
        max_length=3,
        description="Desired tag ids (max 3, preserves order)",
    )

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

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if value is None:
            return None
        seen = set()
        ordered: List[UUID] = []
        for tag_id in value:
            if tag_id in seen:
                continue
            seen.add(tag_id)
            ordered.append(tag_id)
            if len(ordered) >= 3:
                break
        return ordered

    @field_validator("cover_icon")
    @classmethod
    def validate_cover_icon(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if len(normalized) > MAX_COVER_ICON_LENGTH:
            raise ValueError(
                f"cover_icon must be <= {MAX_COVER_ICON_LENGTH} characters"
            )
        if not COVER_ICON_REGEX.match(normalized):
            raise ValueError(
                "cover_icon must contain lowercase letters, digits, or '-'"
            )
        return normalized


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
    maturity: BookMaturity = BookMaturity.SEED
    maturity_score: int = 0
    legacy_flag: bool = False
    manual_maturity_override: bool = False
    manual_maturity_reason: Optional[str] = None
    is_pinned: bool = False
    priority: Optional[int] = None
    urgency: Optional[int] = None
    due_at: Optional[datetime] = None
    last_visited_at: Optional[datetime] = None
    visit_count_90d: int = 0
    soft_deleted_at: Optional[datetime] = None
    block_count: int = 0
    cover_icon: Optional[str] = Field(
        default=None,
        description="Lucide icon name (null → fallback to letter/icon pipeline)"
    )
    cover_media_id: Optional[UUID] = Field(
        default=None,
        description="Media UUID for uploaded cover image (Stable books only)",
    )
    created_at: datetime
    updated_at: datetime
    tags_summary: List[str] = Field(
        default_factory=list,
        description="Ordered tag names (<=3) for badge rendering",
    )
    library_theme_color: Optional[str] = Field(
        default=None,
        description="Library-level theme color (#rrggbb) applied to book covers when provided",
    )

    @classmethod
    def from_domain(cls, book_domain) -> "BookDTO":
        """Convert Book domain object to DTO (RULE-009-013 fields)"""
        maturity = getattr(book_domain, "maturity", BookMaturity.SEED)
        if hasattr(maturity, "value"):
            maturity = maturity.value
        tags = getattr(book_domain, "tags_summary", None)
        normalized_tags = list(tags) if tags else []

        return cls(
            id=book_domain.id,
            library_id=book_domain.library_id,
            bookshelf_id=book_domain.bookshelf_id,
            title=book_domain.title.value,  # Value Object
            summary=book_domain.summary.value if book_domain.summary else None,
            book_type=book_domain.book_type,
            status=book_domain.status,
            maturity=maturity,
            maturity_score=getattr(book_domain, "maturity_score", 0) or 0,
            legacy_flag=bool(getattr(book_domain, "legacy_flag", False)),
            manual_maturity_override=bool(getattr(book_domain, "manual_maturity_override", False)),
            manual_maturity_reason=getattr(book_domain, "manual_maturity_reason", None),
            is_pinned=book_domain.is_pinned,
            priority=book_domain.priority,
            urgency=book_domain.urgency,
            due_at=book_domain.due_at,
            last_visited_at=getattr(book_domain, "last_visited_at", None),
            visit_count_90d=getattr(book_domain, "visit_count_90d", 0) or 0,
            soft_deleted_at=book_domain.soft_deleted_at,
            block_count=book_domain.block_count,
            cover_icon=getattr(book_domain, "cover_icon", None),
            cover_media_id=getattr(book_domain, "cover_media_id", None),
            created_at=book_domain.created_at,
            updated_at=book_domain.updated_at,
            tags_summary=normalized_tags,
            library_theme_color=getattr(book_domain, "library_theme_color", None),
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
            maturity=self.maturity,
            maturity_score=self.maturity_score,
            legacy_flag=self.legacy_flag,
            manual_maturity_override=self.manual_maturity_override,
            manual_maturity_reason=self.manual_maturity_reason,
            is_pinned=self.is_pinned,
            priority=self.priority,
            urgency=self.urgency,
            due_at=self.due_at,
            cover_icon=self.cover_icon,
            cover_media_id=self.cover_media_id,
            block_count=self.block_count,
            last_visited_at=self.last_visited_at,
            visit_count_90d=self.visit_count_90d,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tags_summary=self.tags_summary,
            library_theme_color=self.library_theme_color,
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
            maturity=self.maturity,
            maturity_score=self.maturity_score,
            legacy_flag=self.legacy_flag,
            manual_maturity_override=self.manual_maturity_override,
            manual_maturity_reason=self.manual_maturity_reason,
            is_pinned=self.is_pinned,
            priority=self.priority,
            urgency=self.urgency,
            due_at=self.due_at,
            block_count=self.block_count,
            last_visited_at=self.last_visited_at,
            visit_count_90d=self.visit_count_90d,
            cover_icon=self.cover_icon,
            cover_media_id=self.cover_media_id,
            soft_deleted_at=self.soft_deleted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tags_summary=self.tags_summary,
            library_theme_color=self.library_theme_color,
        )


class BookResponse(BaseModel):
    """Standard Book response (basic fields)"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "library_id": "550e8400-e29b-41d4-a716-446655440099",
                "bookshelf_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "My First Book",
                "summary": "A collection of notes and ideas",
                "book_type": "normal",
                "status": "draft",
                "maturity": "seed",
                "is_pinned": False,
                "priority": 5,
                "urgency": 3,
                "due_at": None,
                "block_count": 12,
                "tags_summary": ["OBSERVATION"],
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    id: UUID
    library_id: UUID
    bookshelf_id: UUID
    title: str
    summary: Optional[str] = None
    book_type: BookType = BookType.NORMAL
    status: BookStatus = BookStatus.DRAFT
    maturity: BookMaturity = BookMaturity.SEED
    maturity_score: int = Field(0, ge=0, le=100, description="Latest maturity score (0-100)")
    legacy_flag: bool = Field(False, description="Legacy partition flag")
    manual_maturity_override: bool = Field(False, description="Whether maturity is manually overridden")
    manual_maturity_reason: Optional[str] = Field(
        None,
        description="Optional note explaining manual override",
    )
    is_pinned: bool
    priority: Optional[int] = None
    urgency: Optional[int] = None
    due_at: Optional[datetime] = None
    cover_icon: Optional[str] = Field(
        default=None,
        description="Lucide icon name or null when UI should use fallback"
    )
    cover_media_id: Optional[UUID] = Field(
        default=None,
        description="Media UUID referencing uploaded cover image"
    )
    block_count: int
    last_visited_at: Optional[datetime] = Field(
        None,
        description="Most recent visit timestamp (chronicle snapshot)",
    )
    visit_count_90d: int = Field(0, ge=0, description="Visit count in trailing 90 days")
    created_at: datetime
    updated_at: datetime
    tags_summary: List[str] = Field(
        default_factory=list,
        description="Tag name badges (ordered, max 3 from API)",
    )
    library_theme_color: Optional[str] = Field(
        default=None,
        description="If set, front-end should use this hex color for book cover accent",
    )


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
                "maturity": "seed",
                "is_pinned": False,
                "priority": 5,
                "urgency": 3,
                "due_at": None,
                "block_count": 12,
                "soft_deleted_at": None,
                "tags_summary": ["OBSERVATION"],
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
                "total": 42,
                "page": 1,
                "page_size": 20,
                "has_more": True,
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "bookshelf_id": "550e8400-e29b-41d4-a716-446655440001",
                        "title": "My First Book",
                        "status": "draft",
                        "maturity": "seed",
                        "is_pinned": False,
                        "block_count": 4,
                        "created_at": "2025-11-13T10:00:00Z",
                        "updated_at": "2025-11-13T10:00:00Z",
                        "tags_summary": ["OBS"],
                    }
                ],
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
