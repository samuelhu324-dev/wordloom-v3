"""
Library Application Output Ports (Repository Interface)

Purpose:
- Define contracts for data persistence (Output Ports)
- Abstraction layer between Domain and Infrastructure
- Repository implementations are in backend/infra/storage/

Implementation:
- Location: backend/infra/storage/library_repository_impl.py
- Implements: ILibraryRepository interface defined here

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_3_repository_interfaces (Line ~600-650)
- HEXAGONAL_RULES.yaml: adapters.outbound_adapters (Line ~160-200)
- DDD_RULES.yaml: library.implementation_layers.persistence_layer
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from api.app.modules.library.domain import Library


# ============================================================================
# Output Port: ILibraryRepository
# ============================================================================

class ILibraryRepository(ABC):
    """
    Repository Port - Data persistence contract for Library aggregate

    Responsibility:
    - Persist Library aggregates (Domain objects) to database
    - Retrieve Library aggregates from database
    - Translate between Domain model and ORM model
    - Handle database constraints and integrity errors

    Design Pattern:
    - Port (this interface) is in application/ layer
    - Adapter (implementation) is in backend/infra/storage/
    - Domain layer has NO dependency on this port
    - Service layer calls Repository via this port interface

    Invariant Enforcement:
    - RULE-001: Enforce unique user_id (one library per user)
    - RULE-002: Enforce user_id is not null
    - RULE-003: Name validation (delegated to Domain, verified at DB level)

    Error Handling:
    - Catch SQLAlchemy exceptions
    - Transform to Domain exceptions (e.g., IntegrityError → LibraryAlreadyExistsError)
    - Log errors at infrastructure level

    Cross-Reference:
    - Related: backend/infra/storage/library_repository_impl.py (implementation)
    - Related: backend/api/app/modules/library/repository.py (current mixed file)
    """

    @abstractmethod
    async def save(self, library: Library) -> None:
        """
        Persist a Library aggregate to database

        Behavior:
        - If library.id is new: INSERT new record
        - If library.id exists: UPDATE existing record

        Args:
            library: Library domain aggregate (contains id, user_id, name, etc.)

        Side Effects:
        - Database: New or updated LibraryModel record
        - Session: Pending transaction (commit handled at Service level)

        Raises:
            LibraryAlreadyExistsError: If unique constraint violated (user_id duplicate)
                This means another library already exists for this user_id (RULE-001 violation)

        Exception:
            Other SQLAlchemy exceptions bubble up and should be caught by caller

        Transaction:
        - Must be transactional (uses SQLAlchemy session)
        - Commit/rollback handled by caller (Service or background task)

        Example:
            library = Library.create(user_id=uuid4(), name="My Library")
            await repository.save(library)
            # Later: session.commit() to persist
        """
        pass

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """
        Retrieve a Library by ID

        Args:
            library_id: UUID of the library

        Returns:
            Library domain aggregate if found, None otherwise
            (Excludes soft-deleted libraries)

        Side Effects:
        - Database: Single SELECT query
        - Session: Adds Library to SQLAlchemy identity map

        Example:
            library = await repository.get_by_id(library_id)
            if library:
                print(f"Found: {library.name.value}")
        """
        pass

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> List[Library]:
        """
        List all Libraries owned by a user (multi-library supported)

        Args:
            user_id: UUID of the user who owns the libraries

        Returns:
            List of Library domain aggregates (excludes soft-deleted libraries)

        Side Effects:
        - Database: SELECT query with WHERE user_id = ?
        - Session: Adds results to SQLAlchemy identity map

        Example:
            libraries = await repository.list_by_user_id(user_id)
        """
        pass

    @abstractmethod
    async def list_overview(
        self,
        *,
        query: Optional[str] = None,
        include_archived: bool = False,
        sort: "LibrarySort" = None,
        pinned_first: bool = True,
    ) -> List[Library]:
        """List libraries with sorting/search options for overview page."""
        pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None:
        """
        Delete a Library by ID (soft delete)

        Behavior:
        - Sets soft_deleted_at timestamp
        - Does NOT remove database record
        - Subsequent queries should exclude soft-deleted libraries

        Args:
            library_id: UUID of the library to delete

        Side Effects:
        - Database: Sets soft_deleted_at timestamp on LibraryModel
        - Session: Marks record as deleted

        Example:
            await repository.delete(library_id)
            # Later: session.commit() to persist

        Note:
        - This is called by Service after Domain has emitted LibraryDeleted event
        - Hard deletion (purge) is handled by separate retention policy job
        """
        pass

    @abstractmethod
    async def exists(self, library_id: UUID) -> bool:
        """
        Check if a Library exists (excluding soft-deleted)

        Args:
            library_id: UUID of the library

        Returns:
            True if library exists and is not soft-deleted, False otherwise

        Side Effects:
        - Database: Efficient EXISTS query (no data transfer)

        Example:
            if not await repository.exists(library_id):
                raise ResourceNotFoundError(f"Library {library_id} not found")
        """
        pass


# ============================================================================
# Output Port: IBookRepository
# ============================================================================

class IBookRepository(ABC):
    """
    Repository Port - Data persistence contract for Book aggregate

    Added for ListBasementBooksUseCase to support querying soft-deleted books.

    Responsibility:
    - Query soft-deleted books (for Basement view)
    - Retrieve books by various criteria

    Cross-Reference:
    - Related: backend/api/app/modules/book/repository.py (if exists)
    - Usage: ListBasementBooksUseCase in library module
    """

    @abstractmethod
    async def find_soft_deleted_by_library(
        self,
        library_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List:
        """
        Query all soft-deleted Books in a Library

        Returns books WHERE library_id=X AND soft_deleted_at IS NOT NULL

        Args:
            library_id: UUID of the library
            limit: Maximum number of books to return (default 100)
            offset: Pagination offset (default 0)

        Returns:
            List of Book domain objects (or ORM models) with soft_deleted_at NOT NULL

        Side Effects:
        - Database: SELECT query with soft_deleted_at IS NOT NULL filter
        - Results ordered by soft_deleted_at DESC (most recently deleted first)

        Example:
            deleted_books = await repository.find_soft_deleted_by_library(
                library_id=lib_id,
                limit=50,
                offset=0
            )
        """
        pass


# ============================================================================
# Output Port: IBookshelfRepository
# ============================================================================

class IBookshelfRepository(ABC):
    """
    Repository Port - Data persistence contract for Bookshelf aggregate

    Added for ListBasementBooksUseCase to fetch Bookshelf names for grouping.

    Responsibility:
    - Retrieve Bookshelf by ID for name lookup
    - Used by ListBasementBooksUseCase to group deleted books

    Cross-Reference:
    - Related: backend/api/app/modules/bookshelf/repository.py
    - Usage: ListBasementBooksUseCase in library module
    """

    @abstractmethod
    async def get_by_id(self, bookshelf_id: UUID) -> Optional:
        """
        Retrieve a Bookshelf by ID

        Args:
            bookshelf_id: UUID of the bookshelf

        Returns:
            Bookshelf domain object if found, None otherwise

        Side Effects:
        - Database: Single SELECT query

        Example:
            bookshelf = await repository.get_by_id(shelf_id)
            if bookshelf:
                print(bookshelf.get_name_value())
        """
        pass


# ============================================================================
# Output Port: ILibraryTagAssociationRepository
# ============================================================================

@dataclass(frozen=True)
class LibraryTagAssociationDTO:
    """Lightweight tag record used to hydrate Plan_31 chips."""

    library_id: UUID
    tag_id: UUID
    tag_name: str
    tag_color: str
    tag_description: Optional[str]
    created_at: datetime


class ILibraryTagAssociationRepository(ABC):
    """Repository contract for Library ↔ Tag associations."""

    @abstractmethod
    async def fetch_option_a_tags(
        self,
        library_ids: List[UUID],
        *,
        limit_per_library: int = 3,
    ) -> List[LibraryTagAssociationDTO]:
        """Return earliest-created tags per Library for chip row rendering."""
        pass

    @abstractmethod
    async def count_tags_by_library(self, library_ids: List[UUID]) -> dict[UUID, int]:
        """Return total tag counts for each Library (Option A +N tooltip)."""
        pass

    @abstractmethod
    async def replace_library_tags(
        self,
        library_id: UUID,
        tag_ids: List[UUID],
        *,
        actor_id: Optional[UUID] = None,
    ) -> None:
        """Replace Library tag associations atomically (used by edit modal)."""
        pass

    @abstractmethod
    async def list_tag_ids(self, library_id: UUID) -> List[UUID]:
        """Return all tag IDs currently linked to the Library."""
        pass


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ILibraryRepository",
    "IBookRepository",
    "IBookshelfRepository",
    "ILibraryTagAssociationRepository",
    "LibraryTagAssociationDTO",
    "LibrarySort",
]


class LibrarySort(str, Enum):
    """Sorting strategy for library overview listing."""

    LAST_ACTIVITY_DESC = "last_activity"
    CREATED_DESC = "created"
    NAME_ASC = "name"
    VIEWS_DESC = "views"

