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
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from api.app.modules.bookshelf.domain import Bookshelf


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class CreateBookshelfRequest:
    """Request to create a new Bookshelf"""
    library_id: UUID
    name: str
    description: Optional[str] = None

    def __post_init__(self):
        """Trim whitespace from string fields"""
        self.name = self.name.strip() if self.name else self.name
        if self.description:
            self.description = self.description.strip()


@dataclass
class GetBookshelfRequest:
    """Request to retrieve a Bookshelf by ID"""
    bookshelf_id: UUID


@dataclass
class DeleteBookshelfRequest:
    """Request to delete (soft delete) a Bookshelf"""
    bookshelf_id: UUID


@dataclass
class RestoreBookshelfRequest:
    """Request to restore a soft-deleted Bookshelf from Basement

    Fields:
    - bookshelf_id: UUID of the bookshelf to restore
    - cascade_restore_books: Whether to restore child books (optional, default False)
    """
    bookshelf_id: UUID
    cascade_restore_books: bool = False


@dataclass
class RenameBookshelfRequest:
    """Request to rename a Bookshelf"""
    bookshelf_id: UUID
    new_name: str

    def __post_init__(self):
        """Trim whitespace from name"""
        self.new_name = self.new_name.strip() if self.new_name else self.new_name


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

    @classmethod
    def from_domain(cls, bookshelf: Bookshelf) -> "CreateBookshelfResponse":
        """Convert domain object to response DTO"""
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=str(bookshelf.name),
            description=str(bookshelf.description) if bookshelf.description else None,
            bookshelf_type=bookshelf.type.value,
            status=bookshelf.status.value,
            created_at=bookshelf.created_at.isoformat() if bookshelf.created_at else "",
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


@dataclass
class GetBasementBookshelvesRequest:
    """Request to list all deleted Bookshelves in a Library

    Fields:
    - library_id: UUID of the library
    - limit: Maximum number of shelves to return (optional, default 100)
    - offset: Pagination offset (optional, default 0)
    """
    library_id: UUID
    limit: int = 100
    offset: int = 0


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
