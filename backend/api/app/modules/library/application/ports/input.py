"""
Library Application Input Ports (UseCase Interfaces)

Purpose:
- Define contracts for all Library use cases (Input Ports)
- Include Request/Response DTOs for each use case
- No implementation details - pure interfaces

Use Cases:
1. CreateLibrary: Create a new library for a user
2. GetLibrary: Retrieve library by ID or user ID
3. DeleteLibrary: Delete/soft-delete a library
4. RenameLibrary: Rename an existing library

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_6_input_ports (Line ~650-680)
- DDD_RULES.yaml: library.implementation_layers.application_layer (Line ~350-420)
- Related: backend/api/app/modules/library/application/use_cases/*.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Input Port: CreateLibraryUseCase
# ============================================================================

@dataclass
class CreateLibraryRequest:
    """
    Request DTO for CreateLibraryUseCase

    Used by Router layer to pass user input to UseCase.
    Validated by Pydantic schema before reaching here.

    Fields:
    - user_id: UUID of the user creating the library
    - name: Name of the library (1-255 characters)
    """
    user_id: UUID
    name: str


@dataclass
class CreateLibraryResponse:
    """
    Response DTO for CreateLibraryUseCase

    Returned by UseCase to Router layer.
    Router converts this to JSON for HTTP response.

    Fields:
    - library_id: UUID of newly created library
    - user_id: UUID of the user
    - name: Name of the library
    - basement_bookshelf_id: UUID of auto-created basement
    - created_at: Creation timestamp
    """
    library_id: UUID
    user_id: UUID
    name: str
    basement_bookshelf_id: UUID
    created_at: datetime


class ICreateLibraryUseCase(ABC):
    """
    Input Port: Create a new Library

    Business Logic:
    1. Validate user exists (Repository check)
    2. Validate user doesn't already have a library (RULE-001)
    3. Validate library name (RULE-003)
    4. Create Library aggregate root
    5. Emit LibraryCreated + BasementCreated events
    6. Persist to database
    7. Return response

    Failure Cases:
    - User already has a library → LibraryAlreadyExistsError (409)
    - Invalid name → ValueError (422)
    - User not found → ResourceNotFoundError (404)

    Cross-Reference:
    - DDD_RULES.yaml: RULE-001 (each user has exactly one Library)
    - DDD_RULES.yaml: RULE-003 (name validation)
    """

    @abstractmethod
    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse:
        """
        Execute the CreateLibrary use case

        Args:
            request: CreateLibraryRequest containing user_id and name

        Returns:
            CreateLibraryResponse with created library details

        Raises:
            LibraryAlreadyExistsError: If user already has a library
            ValueError: If name is invalid
        """
        pass


# ============================================================================
# Input Port: GetLibraryUseCase
# ============================================================================

@dataclass
class GetLibraryRequest:
    """
    Request DTO for GetLibraryUseCase

    Can retrieve by:
    - library_id: Specific library ID
    - user_id: The unique library for a user (RULE-001)
    """
    library_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


@dataclass
class GetLibraryResponse:
    """
    Response DTO for GetLibraryUseCase

    Fields:
    - library_id: UUID of the library
    - user_id: UUID of the owner
    - name: Name of the library
    - basement_bookshelf_id: UUID of auto-created basement
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - is_deleted: Soft delete status
    """
    library_id: UUID
    user_id: UUID
    name: str
    basement_bookshelf_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class IGetLibraryUseCase(ABC):
    """
    Input Port: Retrieve a Library

    Business Logic:
    1. Query by library_id or user_id (exactly one required)
    2. Return library details (excluding soft-deleted)
    3. Handle not found case

    Failure Cases:
    - Library not found → ResourceNotFoundError (404)
    - Both library_id and user_id provided → ValueError (422)
    - Neither provided → ValueError (422)

    Cross-Reference:
    - DDD_RULES.yaml: RULE-001 (user_id lookup returns exactly one library)
    """

    @abstractmethod
    async def execute(self, request: GetLibraryRequest) -> GetLibraryResponse:
        """
        Execute the GetLibrary use case

        Args:
            request: GetLibraryRequest with either library_id or user_id

        Returns:
            GetLibraryResponse with library details

        Raises:
            ResourceNotFoundError: If library not found
            ValueError: If request parameters are invalid
        """
        pass


# ============================================================================
# Input Port: DeleteLibraryUseCase
# ============================================================================

@dataclass
@dataclass
class DeleteLibraryRequest:
    """
    Request DTO for DeleteLibraryUseCase

    Fields:
    - library_id: UUID of the library to delete
    """
    library_id: UUID


class IDeleteLibraryUseCase(ABC):
    """
    Input Port: Delete a Library (soft delete)

    Business Logic:
    1. Verify library exists
    2. Mark library as deleted (soft delete)
    3. Emit LibraryDeleted event (triggers cascade)
    4. Persist soft_deleted_at timestamp
    5. Event handlers will cascade delete:
       - Bookshelves (including all books/blocks)
       - Associated media
       - Associated tags
       - Chronicle entries

    Failure Cases:
    - Library not found → ResourceNotFoundError (404)
    - Already deleted → IllegalStateError (409)

    Side Effects:
    - Emits LibraryDeleted event
    - Event listeners will cascade delete related entities
    - Database: soft_deleted_at timestamp set

    Note: Hard deletion is handled by a separate purge job (retention policy)
    """

    @abstractmethod
    async def execute(self, request: DeleteLibraryRequest) -> None:
        """
        Execute the DeleteLibrary use case

        Args:
            request: DeleteLibraryRequest with library_id

        Returns:
            None

        Raises:
            ResourceNotFoundError: If library not found
            IllegalStateError: If already deleted
        """
        pass


# ============================================================================
# Input Port: RenameLibraryUseCase
# ============================================================================

@dataclass
class RenameLibraryRequest:
    """
    Request DTO for RenameLibraryUseCase

    Fields:
    - library_id: UUID of the library to rename
    - new_name: New name (must be 1-255 characters)
    """
    library_id: UUID
    new_name: str


@dataclass
class RenameLibraryResponse:
    """
    Response DTO for RenameLibraryUseCase

    Fields:
    - library_id: UUID of the library
    - old_name: Previous name
    - new_name: Updated name
    - updated_at: Timestamp of update
    """
    library_id: UUID
    old_name: str
    new_name: str
    updated_at: datetime


class IRenameLibraryUseCase(ABC):
    """
    Input Port: Rename a Library

    Business Logic:
    1. Verify library exists
    2. Validate new name (RULE-003)
    3. Update library name if different
    4. Emit LibraryRenamed event
    5. Persist changes

    Failure Cases:
    - Library not found → ResourceNotFoundError (404)
    - Invalid name → ValueError (422)
    - Already deleted → IllegalStateError (409)

    Cross-Reference:
    - DDD_RULES.yaml: RULE-003 (name validation)
    """

    @abstractmethod
    async def execute(self, request: RenameLibraryRequest) -> RenameLibraryResponse:
        """
        Execute the RenameLibrary use case

        Args:
            request: RenameLibraryRequest with library_id and new_name

        Returns:
            RenameLibraryResponse with rename details

        Raises:
            ResourceNotFoundError: If library not found
            ValueError: If name is invalid
            IllegalStateError: If library is already deleted
        """
        pass


# ============================================================================
# Input Port: RestoreLibraryUseCase (NEW - Nov 14, 2025)
# ============================================================================

@dataclass
class RestoreLibraryRequest:
    """
    Request DTO for RestoreLibraryUseCase

    Used to restore a soft-deleted Library from Basement.

    Fields:
    - library_id: UUID of the library to restore
    """
    library_id: UUID


@dataclass
class RestoreLibraryResponse:
    """
    Response DTO for RestoreLibraryUseCase

    Returned when library is successfully restored.

    Fields:
    - library_id: UUID of restored library
    - restored_at: Timestamp of restoration
    - message: Human-readable confirmation message
    """
    library_id: UUID
    restored_at: datetime
    message: str


class IRestoreLibraryUseCase(ABC):
    """
    Input Port: Restore a soft-deleted Library from Basement

    Business Logic:
    1. Load Library from repository (by library_id)
    2. Check if library is actually deleted (soft_deleted_at not null)
    3. Call Library.restore() to emit LibraryRestored event
    4. Publish event to EventBus
    5. Persist restoration to database
    6. Return response

    Failure Cases:
    - Library not found → ResourceNotFoundError (404)
    - Library not deleted → IllegalStateError (400)

    Invariants:
    - BASEMENT-001: Library is root aggregate, no parent dependency check needed

    Cross-Reference:
    - DDD_RULES.yaml: deletion_recovery_framework.basement.recovery_rules
    - ADR-038: Deletion & Recovery Unified Framework
    """

    @abstractmethod
    async def execute(self, request: RestoreLibraryRequest) -> RestoreLibraryResponse:
        """
        Execute the RestoreLibrary use case

        Args:
            request: RestoreLibraryRequest with library_id

        Returns:
            RestoreLibraryResponse with restoration details

        Raises:
            ResourceNotFoundError: If library not found
            IllegalStateError: If library is not deleted
        """
        pass


# ============================================================================
# Input Port: ListBasementBooksUseCase (NEW - Nov 14, 2025)
# ============================================================================

@dataclass
class BasementBookItem:
    """
    DTO representing a single deleted Book in Basement

    Fields:
    - book_id: UUID of the book
    - title: Title of the book
    - bookshelf_id: Original Bookshelf ID (preserved from before deletion)
    - bookshelf_name: Name of original Bookshelf (for display)
    - soft_deleted_at: When the book was deleted
    """
    book_id: UUID
    title: str
    bookshelf_id: UUID
    bookshelf_name: str
    soft_deleted_at: datetime


@dataclass
class BasementShelfGroup:
    """
    DTO representing a group of deleted Books organized by original Bookshelf

    Groups deleted Books by their original bookshelf_id, preserving the
    relationship information even though the books are soft-deleted.

    Fields:
    - bookshelf_id: UUID of the original Bookshelf
    - bookshelf_name: Name of original Bookshelf
    - book_count: Number of deleted books in this group
    - books: Array of BasementBookItem
    """
    bookshelf_id: UUID
    bookshelf_name: str
    book_count: int
    books: list  # List[BasementBookItem]


@dataclass
class ListBasementBooksRequest:
    """
    Request DTO for ListBasementBooksUseCase

    Used to query all soft-deleted Books in a Library.

    Fields:
    - library_id: UUID of the library
    - limit: Maximum number of books to return per shelf (optional, default 100)
    - offset: Pagination offset (optional, default 0)
    """
    library_id: UUID
    limit: int = 100
    offset: int = 0


@dataclass
class ListBasementBooksResponse:
    """
    Response DTO for ListBasementBooksUseCase

    Returns grouped list of deleted Books.

    Fields:
    - library_id: UUID of the library
    - total_count: Total number of deleted books in library
    - shelf_groups: Array of BasementShelfGroup with deleted books
    - message: Human-readable summary message
    """
    library_id: UUID
    total_count: int
    shelf_groups: list  # List[BasementShelfGroup]
    message: str


class IListBasementBooksUseCase(ABC):
    """
    Input Port: List all soft-deleted Books in a Library (Basement view)

    Business Logic:
    1. Query all Books WHERE library_id=X AND soft_deleted_at IS NOT NULL
    2. Group results by original bookshelf_id
    3. For each group, fetch Bookshelf name for display
    4. Return BasementShelfGroup[] with nested BasementBookItem[]
    5. Handle case where original Bookshelf is deleted or missing

    Invariants:
    - BASEMENT-002: Doesn't move data, just queries with grouping
    - BASEMENT-003: Preserves original bookshelf_id relationships

    Failure Cases:
    - Library not found → ResourceNotFoundError (404)

    Cross-Reference:
    - DDD_RULES.yaml: deletion_recovery_framework.basement
    - ADR-038: Deletion & Recovery Unified Framework, Basement Pattern
    """

    @abstractmethod
    async def execute(self, request: ListBasementBooksRequest) -> ListBasementBooksResponse:
        """
        Execute the ListBasementBooks use case

        Args:
            request: ListBasementBooksRequest with library_id and pagination

        Returns:
            ListBasementBooksResponse with grouped deleted books

        Raises:
            ResourceNotFoundError: If library not found
        """
        pass


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # CreateLibrary
    "CreateLibraryRequest",
    "CreateLibraryResponse",
    "ICreateLibraryUseCase",
    # GetLibrary
    "GetLibraryRequest",
    "GetLibraryResponse",
    "IGetLibraryUseCase",
    # DeleteLibrary
    "DeleteLibraryRequest",
    "IDeleteLibraryUseCase",
    # RenameLibrary
    "RenameLibraryRequest",
    "RenameLibraryResponse",
    "IRenameLibraryUseCase",
    # RestoreLibrary (NEW)
    "RestoreLibraryRequest",
    "RestoreLibraryResponse",
    "IRestoreLibraryUseCase",
    # ListBasementBooks (NEW)
    "BasementBookItem",
    "BasementShelfGroup",
    "ListBasementBooksRequest",
    "ListBasementBooksResponse",
    "IListBasementBooksUseCase",
]
