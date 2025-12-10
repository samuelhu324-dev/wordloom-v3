"""
Library Schemas - Pydantic v2 models for API validation and serialization

Used for:
- Request/response validation in FastAPI
- Serialization of Domain models
- Documentation generation
- Round-trip testing and data consistency

Corresponds to DDD_RULES:
  - RULE-001: Library 1:1 association with User
  - RULE-002: Library.user_id must be valid
  - RULE-003: Library name constraints (1-255 chars)
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List
from enum import Enum


# ============================================
# Enums
# ============================================

class LibraryStatus(str, Enum):
    """Library status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LibraryTagSummary(BaseModel):
    """Lightweight tag payload for Library cards (Plan_31 Option A chips)."""

    id: UUID = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag label shown on chip")
    color: str = Field(
        "#F3F4F6",
        description="Hex color; Option A uses low-saturation greys by default",
    )
    description: Optional[str] = Field(
        None,
        description="Tooltip/message sourced from Tag 管理里的“描述”字段",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "翻译实验室",
                "color": "#F3F4F6",
                "description": "Specific for software development.",
            }
        }
    )


class LibraryTagsUpdate(BaseModel):
    """Request payload for replacing Library tags via API."""

    tag_ids: List[UUID] = Field(
        default_factory=list,
        description="完整的标签 ID 列表；若为空表示清空所有标签",
    )


class LibraryTagsResponse(BaseModel):
    """Response payload describing a Library's tags."""

    library_id: UUID = Field(..., description="Library ID")
    tag_ids: List[UUID] = Field(default_factory=list, description="全部标签 ID")
    tags: List[LibraryTagSummary] = Field(
        default_factory=list,
        description="Option A 限制下展示的标签 chips",
    )
    tag_total_count: int = Field(0, ge=0, description="总标签数量")


# ============================================
# Request Schemas (API Input)
# ============================================

class LibraryCreate(BaseModel):
    """Schema for creating a new Library

    RULE-001: Each user can have exactly one Library
    RULE-003: Library name must be 1-255 characters, non-empty
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Library name (uniqueness enforced per user)",
        examples=["My Personal Knowledge Base", "工作笔记库"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional library description (≤500 chars)",
    )
    theme_color: Optional[str] = Field(
        None,
        description="Explicit theme color hex value (e.g. #1a9bd7)",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Validate name is not empty or whitespace-only"""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Library name cannot be empty or whitespace only")
        return v

    @field_validator("theme_color", mode="before")
    @classmethod
    def normalize_theme_color(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_theme_color(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My Personal Library"
            }
        }
    )


class LibraryUpdate(BaseModel):
    """Schema for updating Library

    RULE-003: Name validation applies if provided
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New Library name (optional)",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated description (send empty string to clear)",
    )
    cover_media_id: Optional[UUID] = Field(
        None,
        description="Associated cover media ID (optional)",
    )
    pinned: Optional[bool] = Field(
        None,
        description="Whether the library is pinned to the top segment",
    )
    pinned_order: Optional[int] = Field(
        None,
        ge=0,
        description="Ordering index inside pinned segment (lower = higher)",
    )
    archived: Optional[bool] = Field(
        None,
        description="Archive toggle. True → archive, False → restore.",
    )
    theme_color: Optional[str] = Field(
        None,
        description="Explicit theme color hex value; send null to clear",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """Validate name only if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Library name cannot be empty or whitespace only")
        return v

    @field_validator("theme_color", mode="before")
    @classmethod
    def normalize_theme_color(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_theme_color(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Library Name"
            }
        }
    )


# ============================================
# Response Schemas (API Output)
# ============================================

class LibraryResponse(BaseModel):
    """Basic Library response (for lists, brief display)

    RULE-001: Includes user_id (1:1 relationship)
    """
    id: UUID = Field(..., description="Library global unique ID")
    user_id: UUID = Field(..., description="Owner User ID (1:1 relationship per RULE-001)")
    name: str = Field(..., description="Library name")
    description: Optional[str] = Field(None, description="Library description (optional)")
    cover_media_id: Optional[UUID] = Field(None, description="Cover media UUID (if set)")
    theme_color: Optional[str] = Field(None, description="Explicit theme color hex value (#rrggbb)")
    pinned: bool = Field(False, description="Pinned to top segment")
    pinned_order: Optional[int] = Field(None, description="Pinned ordering index")
    archived_at: Optional[datetime] = Field(None, description="Timestamp when archived")
    last_activity_at: datetime = Field(..., description="Last activity timestamp driving default sort")
    views_count: int = Field(0, description="Total library views")
    last_viewed_at: Optional[datetime] = Field(None, description="Most recent view timestamp")
    tags: List[LibraryTagSummary] = Field(
        default_factory=list,
        description="Plan_31 Option A tag chips (最多展示 3 个；超出由客户端 +N 显示)",
    )
    tag_total_count: int = Field(
        0,
        ge=0,
        description="Total tags linked to this library (Option A +N tooltip)",
    )
    basement_bookshelf_id: Optional[UUID] = Field(
        None,
        description="Basement Bookshelf ID (RULE-010 recycle bin)",
    )
    created_at: datetime = Field(..., description="Creation time (ISO 8601)")
    updated_at: datetime = Field(..., description="Last modification time (ISO 8601)")

    model_config = ConfigDict(
        from_attributes=True,  # Pydantic v2 ORM mode
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        },
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "My Personal Library",
                "basement_bookshelf_id": "750e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-15T10:30:00+00:00",
                "updated_at": "2025-01-15T10:30:00+00:00",
            }
        }
    )


class LibraryDetailResponse(LibraryResponse):
    """Detailed Library response (includes metadata and statistics)"""
    # Statistics (calculated from Service layer)
    bookshelf_count: int = Field(
        0,
        description="Count of direct Bookshelves (excluding Basement per RULE-010)",
        ge=0,
    )
    # Extended info
    status: LibraryStatus = Field(
        LibraryStatus.ACTIVE,
        description="Library status",
    )
    # description & cover_media_id inherited from LibraryResponse

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "My Personal Library",
                "created_at": "2025-01-15T10:30:00+00:00",
                "updated_at": "2025-01-15T10:30:00+00:00",
                "bookshelf_count": 5,
                "basement_bookshelf_id": "750e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "description": "我的个人知识库",
            }
        }
    )


class LibraryPaginatedResponse(BaseModel):
    """Paginated Library response"""
    items: List[LibraryDetailResponse] = Field(
        ...,
        description="List of Libraries",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total record count",
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Records per page",
    )
    has_more: bool = Field(
        ...,
        description="Whether next page exists",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }
        }
    )


# ============================================
# DTO (Data Transfer Object) - Internal Use
# ============================================

class LibraryDTO(BaseModel):
    """Internal DTO (Service ↔ Repository)

    Used for passing data between Service and Repository layers
    without exposing ORM models directly.
    """
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    basement_bookshelf_id: Optional[UUID] = None
    status: LibraryStatus = LibraryStatus.ACTIVE

    @classmethod
    def from_domain(cls, library):
        """Convert from Domain object (ORM Model → DTO)"""
        return cls(
            id=library.id,
            user_id=library.user_id,
            name=library.name,
            created_at=library.created_at,
            updated_at=library.updated_at,
            basement_bookshelf_id=getattr(library, "basement_bookshelf_id", None),
            status=getattr(library, "status", LibraryStatus.ACTIVE),
        )

    def to_response(self) -> LibraryResponse:
        """Convert to API response (DTO → Response)"""
        return LibraryResponse(**self.model_dump())

    def to_detail_response(self, bookshelf_count: int = 0) -> LibraryDetailResponse:
        """Convert to detailed API response with statistics"""
        data = self.model_dump()
        data["bookshelf_count"] = bookshelf_count
        return LibraryDetailResponse(**data)


def _normalize_theme_color(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Theme color must be a string")
    trimmed = value.strip()
    if not trimmed:
        return None
    if not trimmed.startswith('#'):
        trimmed = f'#' + trimmed
    hex_part = trimmed[1:]
    if len(hex_part) == 3:
        if not _is_hex(hex_part):
            raise ValueError("Theme color must be hex digits (e.g. #abc or #aabbcc)")
        hex_part = ''.join(ch * 2 for ch in hex_part)
    elif len(hex_part) == 6:
        if not _is_hex(hex_part):
            raise ValueError("Theme color must be hex digits (e.g. #abc or #aabbcc)")
    else:
        raise ValueError("Theme color must be 3 or 6 hex digits")
    return f"#{hex_part.lower()}"


def _is_hex(value: str) -> bool:
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


# ============================================
# Round-trip Validation Support
# ============================================

class LibraryRoundTripValidator(BaseModel):
    """Validator for round-trip data consistency testing

    Used in integration tests to ensure:
    - Data → JSON → Data consistency
    - Data → DB → Data consistency
    - All fields preserved through full cycle
    """
    original: LibraryDetailResponse
    from_dict: LibraryDetailResponse
    from_db: LibraryDetailResponse

    def validate_consistency(self) -> Dict[str, bool]:
        """Check data consistency across all conversion methods"""
        return {
            "id_consistent": (
                self.original.id == self.from_dict.id == self.from_db.id
            ),
            "user_id_consistent": (
                self.original.user_id == self.from_dict.user_id == self.from_db.user_id
            ),
            "name_consistent": (
                self.original.name == self.from_dict.name == self.from_db.name
            ),
            "timestamps_consistent": (
                self.original.created_at == self.from_db.created_at
                and self.original.updated_at == self.from_db.updated_at
            ),
            "status_consistent": (
                self.original.status == self.from_dict.status == self.from_db.status
            ),
        }

    def all_consistent(self) -> bool:
        """Whether all fields are consistent"""
        return all(self.validate_consistency().values())

    def get_inconsistencies(self) -> List[str]:
        """Get list of inconsistent fields"""
        consistency = self.validate_consistency()
        return [key for key, value in consistency.items() if not value]


# ============================================
# Error Response Schema
# ============================================

class ErrorDetail(BaseModel):
    """Structured error response detail"""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context and details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "LIBRARY_NOT_FOUND",
                "message": "Library not found: 550e8400-e29b-41d4-a716-446655440000",
                "details": {
                    "library_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": None
                }
            }
        }
    )
