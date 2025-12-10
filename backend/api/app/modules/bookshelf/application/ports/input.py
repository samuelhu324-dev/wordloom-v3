"""
Bookshelf Input Ports - UseCase Interfaces & DTOs

Defines all Bookshelf UseCase contracts for Router layer.
Pattern: Command-Query separation (4 core UseCases)

Design:
- Request/Response are data classes for serialization
- UseCase interfaces are abstract contracts
- No circular imports - DTOs don't import domain
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from uuid import UUID
from dataclasses import dataclass, field  # Added missing import to enable @dataclass usage

from api.app.modules.bookshelf.domain import Bookshelf, BookshelfStatus


# ============================================================================
# Input DTOs (Request Models - Pydantic v2)
# ============================================================================

class CreateBookshelfRequest(BaseModel):
    """Request to create a new Bookshelf"""
    library_id: UUID = Field(..., description="UUID of the library")
    name: str = Field(..., min_length=1, max_length=255, description="Bookshelf name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    tag_ids: Optional[List[UUID]] = Field(
        None,
        description="Initial tag IDs to associate (order preserved, max 3)",
    )

    @field_validator('name', 'description', mode='before')
    @classmethod
    def trim_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from string fields"""
        if isinstance(v, str):
            v = v.strip() or None
        return v

    @field_validator('tag_ids', mode='after')
    @classmethod
    def validate_tag_ids(cls, value: Optional[List[UUID]]) -> Optional[List[UUID]]:
        """Ensure tag selections stay unique and within limit"""
        if value is None:
            return None
        unique: List[UUID] = []
        seen = set()
        for tag_id in value:
            if tag_id in seen:
                continue
            unique.append(tag_id)
            seen.add(tag_id)
        if len(unique) > 3:
            raise ValueError("tag_ids cannot contain more than 3 items")
        return unique


class GetBookshelfRequest(BaseModel):
    """Request to retrieve a Bookshelf by ID"""
    bookshelf_id: UUID = Field(..., description="UUID of the bookshelf")


class ListBookshelvesRequest(BaseModel):
    """Request to list Bookshelves for a library"""
    library_id: UUID = Field(..., description="UUID of the library")
    skip: int = Field(0, ge=0, description="Pagination skip")
    limit: int = Field(100, ge=1, le=100, description="Pagination limit")
    include_deleted: bool = Field(False, description="Include deleted items")


class GetBasementRequest(BaseModel):
    """Request to retrieve the Basement bookshelf for a library"""
    library_id: UUID = Field(..., description="UUID of the library")


class DeleteBookshelfRequest(BaseModel):
    """Request to delete (soft delete) a Bookshelf"""
    bookshelf_id: UUID = Field(..., description="UUID of the bookshelf")


class RestoreBookshelfRequest(BaseModel):
    """Request to restore a soft-deleted Bookshelf from Basement

    Fields:
    - bookshelf_id: UUID of the bookshelf to restore
    - cascade_restore_books: Whether to restore child books (optional, default False)
    """
    bookshelf_id: UUID = Field(..., description="UUID of the bookshelf to restore")
    cascade_restore_books: bool = Field(False, description="Cascade restore child books")


class RenameBookshelfRequest(BaseModel):
    """Request to rename a Bookshelf"""
    bookshelf_id: UUID = Field(..., description="UUID of the bookshelf")
    new_name: str = Field(..., min_length=1, max_length=255, description="New name")

    @field_validator('new_name', mode='before')
    @classmethod
    def trim_name(cls, v: str) -> str:
        """Trim whitespace from name"""
        return v.strip() if isinstance(v, str) else v


class UpdateBookshelfRequest(BaseModel):
    """Request to update a Bookshelf (name and/or description)"""
    bookshelf_id: Optional[UUID] = Field(None, description="UUID of the bookshelf")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New name")
    description: Optional[str] = Field(None, max_length=1000, description="New description")
    status: Optional[BookshelfStatus] = Field(
        None,
        description="New status (active or archived)",
    )
    is_pinned: Optional[bool] = Field(
        None,
        description="Toggle pinned state",
    )
    tag_ids: Optional[List[UUID]] = Field(
        None,
        description="Full replacement list of associated Tag IDs (max 3)",
    )

    @field_validator('name', 'description', mode='before')
    @classmethod
    def trim_fields(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from string fields"""
        if isinstance(v, str):
            v = v.strip() or None
        return v

    @field_validator('bookshelf_id')
    @classmethod
    def ensure_bookshelf_id_placeholder(cls, value: Optional[UUID]) -> Optional[UUID]:
        """Allow router to hydrate bookshelf_id later, but reject empty strings."""
        if value == "":
            raise ValueError("bookshelf_id cannot be blank")
        return value

    @field_validator('tag_ids', mode='after')
    @classmethod
    def validate_tag_ids(cls, value: Optional[List[UUID]]) -> Optional[List[UUID]]:
        """Ensure we keep ≤3 unique tag ids while preserving order"""
        if value is None:
            return None
        unique: List[UUID] = []
        seen = set()
        for tag_id in value:
            if tag_id in seen:
                continue
            unique.append(tag_id)
            seen.add(tag_id)
        if len(unique) > 3:
            raise ValueError("tag_ids cannot contain more than 3 items")
        return unique


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class CreateBookshelfResponse:
    """Response after creating a Bookshelf"""
    id: UUID
    library_id: UUID
    name: str
    description: Optional[str]
    bookshelf_type: str  # "REGULAR" or "BASEMENT"
    status: str  # "ACTIVE", "ARCHIVED", "DELETED"
    created_at: str
    is_pinned: bool
    is_favorite: bool
    is_basement: bool
    tag_ids: List[UUID] = field(default_factory=list)
    tags_summary: List[str] = field(default_factory=list)

    @classmethod
    def from_domain(
        cls,
        bookshelf: Bookshelf,
        *,
        tag_ids: Optional[List[UUID]] = None,
        tags_summary: Optional[List[str]] = None,
    ) -> "CreateBookshelfResponse":
        """Convert domain object to response DTO"""
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=str(bookshelf.name),
            description=str(bookshelf.description) if bookshelf.description else None,
            bookshelf_type=bookshelf.type.value,
            status=bookshelf.status.value,
            created_at=bookshelf.created_at.isoformat() if bookshelf.created_at else "",
            is_pinned=bookshelf.is_pinned,
            is_favorite=bookshelf.is_favorite,
            is_basement=bookshelf.is_basement,
            tag_ids=tag_ids or [],
            tags_summary=tags_summary or [],
        )


@dataclass
class GetBookshelfResponse:
    """Response when retrieving a Bookshelf"""
    id: UUID
    library_id: UUID
    name: str
    description: Optional[str]
    bookshelf_type: str
    status: str
    is_pinned: bool
    is_favorite: bool
    is_basement: bool
    created_at: str
    updated_at: Optional[str]

    @classmethod
    def from_domain(cls, bookshelf: Bookshelf) -> "GetBookshelfResponse":
        """Convert domain object to response DTO"""
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=str(bookshelf.name),
            description=str(bookshelf.description) if bookshelf.description else None,
            bookshelf_type=bookshelf.type.value,
            status=bookshelf.status.value,
            is_pinned=bookshelf.is_pinned,
            is_favorite=bookshelf.is_favorite,
            is_basement=bookshelf.is_basement,
            created_at=bookshelf.created_at.isoformat() if bookshelf.created_at else "",
            updated_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else None,
        )


@dataclass
class DeleteBookshelfResponse:
    """Response after deleting (soft delete) a Bookshelf"""
    id: UUID
    status: str  # Will be "DELETED"
    deleted_at: str


@dataclass
class RestoreBookshelfResponse:
    """Response after restoring a soft-deleted Bookshelf from Basement

    Fields:
    - id: UUID of restored bookshelf
    - status: New status (will be "ACTIVE")
    - restored_at: Timestamp of restoration
    - restored_books_count: Number of child books restored (if cascade_restore_books=True)
    - message: Human-readable confirmation message
    """
    id: UUID
    status: str
    restored_at: str
    restored_books_count: int = 0
    message: str = ""


@dataclass
class RenameBookshelfResponse:
    """Response after renaming a Bookshelf"""
    id: UUID
    name: str
    updated_at: str

    @classmethod
    def from_domain(cls, bookshelf: Bookshelf) -> "RenameBookshelfResponse":
        """Convert domain object to response DTO"""
        return cls(
            id=bookshelf.id,
            name=str(bookshelf.name),
            updated_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else "",
        )


# Generic bookshelf response alias for router use
BookshelfResponse = CreateBookshelfResponse


@dataclass
class UpdateBookshelfResponse:
    """Response after updating a Bookshelf, including tag summary"""

    id: UUID
    library_id: UUID
    name: str
    description: Optional[str]
    status: str
    is_pinned: bool
    is_favorite: bool
    is_basement: bool
    created_at: str
    updated_at: Optional[str]
    tag_ids: List[UUID]
    tags_summary: List[str]

    @classmethod
    def from_domain(
        cls,
        bookshelf: Bookshelf,
        *,
        tag_ids: List[UUID],
        tags_summary: List[str],
    ) -> "UpdateBookshelfResponse":
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=str(bookshelf.name),
            description=str(bookshelf.description) if bookshelf.description else None,
            status=bookshelf.status.value,
            is_pinned=bookshelf.is_pinned,
            is_favorite=bookshelf.is_favorite,
            is_basement=bookshelf.is_basement,
            created_at=bookshelf.created_at.isoformat() if bookshelf.created_at else "",
            updated_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else None,
            tag_ids=tag_ids,
            tags_summary=tags_summary,
        )


# ============================================================================
# UseCase Input Ports (Interfaces)
# ============================================================================

class ICreateBookshelfUseCase(ABC):
    """UseCase: Create a new Bookshelf in a Library

    Responsibilities:
    - Validate input (name length, library exists)
    - Check name uniqueness per library (RULE-006)
    - Create Bookshelf domain object
    - Persist to repository
    - Return response with created bookshelf data

    RULE-006: Bookshelf names must be unique per Library (1-255 chars)
    RULE-004: Libraries can contain unlimited bookshelves
    """

    @abstractmethod
    async def execute(self, request: CreateBookshelfRequest) -> CreateBookshelfResponse:
        """Execute bookshelf creation"""
        pass


class IGetBookshelfUseCase(ABC):
    """UseCase: Retrieve a Bookshelf by ID

    Responsibilities:
    - Load bookshelf from repository by ID
    - Return bookshelf data or raise BookshelfNotFoundError
    - Support all status types (ACTIVE, ARCHIVED, DELETED)
    """

    @abstractmethod
    async def execute(self, request: GetBookshelfRequest) -> GetBookshelfResponse:
        """Execute bookshelf retrieval"""
        pass


class IDeleteBookshelfUseCase(ABC):
    """UseCase: Delete (soft delete) a Bookshelf

    Responsibilities:
    - Load bookshelf by ID
    - Validate not Basement type (RULE-010)
    - Call bookshelf.mark_deleted() to change status
    - Persist to repository
    - Publish deletion event

    RULE-010: Basement bookshelf cannot be deleted (recycle bin)
    RULE-005: Deletion is soft (status → DELETED)
    """

    @abstractmethod
    async def execute(self, request: DeleteBookshelfRequest) -> DeleteBookshelfResponse:
        """Execute bookshelf deletion"""
        pass


class IRestoreBookshelfUseCase(ABC):
    """UseCase: Restore a soft-deleted Bookshelf from Basement

    Responsibilities:
    - Load bookshelf by ID
    - Verify bookshelf is in DELETED status
    - Verify parent Library is not deleted (BASEMENT-001 invariant)
    - Call bookshelf.restore() to change status back to ACTIVE
    - Optionally cascade-restore child books (if cascade_restore_books=True)
    - Persist to repository
    - Publish restoration event

    Invariants:
    - BASEMENT-001: Cannot restore child Bookshelf if parent Library is deleted
    - BASEMENT-002: Restoration doesn't move data, just updates status

    Related:
    - DDD_RULES.yaml: deletion_recovery_framework.basement.recovery_rules
    - ADR-038: Deletion & Recovery Unified Framework
    """

    @abstractmethod
    async def execute(self, request: RestoreBookshelfRequest) -> RestoreBookshelfResponse:
        """Execute bookshelf restoration

        Args:
            request: RestoreBookshelfRequest with bookshelf_id and cascade_restore_books

        Returns:
            RestoreBookshelfResponse with restoration details

        Raises:
            BookshelfNotFoundError: If bookshelf not found
            LibraryDeletedError: If parent Library is deleted (BASEMENT-001)
            IllegalStateError: If bookshelf is not in DELETED status
        """
        pass


class IRenameBookshelfUseCase(ABC):
    """UseCase: Rename a Bookshelf

    Responsibilities:
    - Load bookshelf by ID
    - Validate new name (length, not duplicate per library)
    - Call bookshelf.rename(new_name) to update name
    - Persist to repository
    - Publish renamed event

    RULE-006: New name must be unique within same library
    """

    @abstractmethod
    async def execute(self, request: RenameBookshelfRequest) -> RenameBookshelfResponse:
        """Execute bookshelf rename"""
        pass


class IUpdateBookshelfUseCase(ABC):
    """UseCase: Update Bookshelf metadata (name/description/status/tags)"""

    @abstractmethod
    async def execute(self, request: UpdateBookshelfRequest) -> UpdateBookshelfResponse:
        """Execute bookshelf update"""
        pass


# ============================================================================
# GetBasementBookshelves - NEW (Nov 14, 2025)
# ============================================================================

@dataclass
class BasementBookshelfItem:
    """
    DTO representing a single deleted Bookshelf in Basement

    Fields:
    - id: UUID of the bookshelf
    - library_id: UUID of parent library
    - name: Name of the bookshelf
    - orphaned_books_count: Number of books in this shelf (without children)
    - status: Will be "DELETED"
    - deleted_at: When the bookshelf was deleted
    """
    id: UUID
    library_id: UUID
    name: str
    orphaned_books_count: int
    status: str
    deleted_at: str


class GetBasementBookshelvesRequest(BaseModel):
    """Request to list all deleted Bookshelves in a Library

    Fields:
    - library_id: UUID of the library
    - limit: Maximum number of shelves to return (optional, default 100)
    - offset: Pagination offset (optional, default 0)
    """
    library_id: UUID = Field(..., description="UUID of the library")
    limit: int = Field(100, ge=1, le=100, description="Result limit")
    offset: int = Field(0, ge=0, description="Pagination offset")


@dataclass
class GetBasementBookshelvesResponse:
    """Response containing list of deleted Bookshelves

    Fields:
    - library_id: UUID of the library
    - total_count: Total number of deleted shelves
    - bookshelves: List of BasementBookshelfItem
    - message: Human-readable summary
    """
    library_id: UUID
    total_count: int
    bookshelves: list  # List[BasementBookshelfItem]
    message: str


class IGetBasementBookshelvesUseCase(ABC):
    """UseCase: List all deleted Bookshelves in a Library (Basement view)

    Responsibilities:
    - Query all Bookshelves WHERE status=DELETED in library
    - For each, count orphaned books (Blocks without parent Books?)
    - Support pagination
    - Return BasementBookshelfItem[] with counts

    Related:
    - DDD_RULES.yaml: deletion_recovery_framework.basement
    - ADR-038: Deletion & Recovery Unified Framework
    """

    @abstractmethod
    async def execute(self, request: GetBasementBookshelvesRequest) -> GetBasementBookshelvesResponse:
        """Execute get basement bookshelves

        Args:
            request: GetBasementBookshelvesRequest with library_id and pagination

        Returns:
            GetBasementBookshelvesResponse with list of deleted shelves

        Raises:
            ValueError: If library not found
        """
        pass


# ============================================================================
# Dashboard Request DTOs (Bookshelf Overview)
# ============================================================================


class BookshelfDashboardSort(str, Enum):
    """Sorting options for Bookshelf dashboard"""

    RECENT_ACTIVITY = "recent_activity"
    NAME_ASC = "name_asc"
    CREATED_DESC = "created_desc"
    BOOK_COUNT_DESC = "book_count_desc"


class BookshelfDashboardFilter(str, Enum):
    """Filter options for Bookshelf dashboard"""

    ALL = "all"
    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"
    PINNED = "pinned"


class BookshelfDashboardRequest(BaseModel):
    """Request payload for Bookshelf dashboard summary list"""

    library_id: UUID = Field(..., description="UUID of the library")
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort: BookshelfDashboardSort = Field(
        BookshelfDashboardSort.RECENT_ACTIVITY,
        description="Sorting mode",
    )
    status_filter: BookshelfDashboardFilter = Field(
        BookshelfDashboardFilter.ACTIVE,
        description="Filter by status/health",
    )

