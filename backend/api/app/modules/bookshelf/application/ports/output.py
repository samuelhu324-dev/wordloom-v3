"""
Bookshelf Repository Output Port

Abstract interface for Bookshelf persistence adapter.
Implementation: infra/storage/bookshelf_repository_impl.py

Design Pattern: Hexagonal Architecture (Ports & Adapters)
- Port: This interface defines the contract
- Adapter: SQLAlchemyBookshelfRepository implements this contract
- Benefit: Domain layer doesn't depend on ORM or database implementation
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from api.app.modules.bookshelf.domain import Bookshelf


class IBookshelfRepository(ABC):
    """
    Abstract Repository for Bookshelf persistence

    Responsibilities:
    - Define CRUD operations on Bookshelf aggregate
    - Query operations: get by ID, by library, basement lookup
    - Existence checks and name validation
    - Abstract from ORM implementation details

    Note: All methods are async for async/await support
    """

    @abstractmethod
    async def save(self, bookshelf: Bookshelf) -> None:
        """
        Save (create or update) a Bookshelf aggregate to database

        Args:
            bookshelf: Bookshelf domain object to persist

        Raises:
            BookshelfAlreadyExistsError: If name already exists in same library (RULE-006)

        Design: Accept domain object, not ORM model
        """
        pass

    @abstractmethod
    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        """
        Retrieve a Bookshelf by its ID

        Args:
            bookshelf_id: UUID of the bookshelf

        Returns:
            Bookshelf domain object if found, None otherwise

        Design: Return domain object, not ORM model
        """
        pass

    @abstractmethod
    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        """
        Retrieve all active (non-deleted) Bookshelves in a Library

        RULE-004: Each Library can contain unlimited Bookshelves
        RULE-005: Returns only ACTIVE bookshelves

        Args:
            library_id: UUID of the library

        Returns:
            List of Bookshelf domain objects (empty list if none found)

        Design: Automatically filters DELETED status
        """
        pass

    @abstractmethod
    async def get_basement_by_library_id(self, library_id: UUID) -> Optional[Bookshelf]:
        """
        Retrieve the special Basement Bookshelf for a Library

        RULE-010: Each Library has at most one Basement (recycle bin)
        Basement type is BASEMENT, never deleted

        Args:
            library_id: UUID of the library

        Returns:
            Basement Bookshelf if exists, None otherwise
        """
        pass

    @abstractmethod
    async def exists_by_name(self, library_id: UUID, name: str) -> bool:
        """
        Check if a Bookshelf with given name already exists in Library

        RULE-006: Bookshelf names must be unique per Library

        Args:
            library_id: UUID of the library
            name: Bookshelf name to check (will be trimmed)

        Returns:
            True if name exists (active bookshelves only), False otherwise

        Design: Used for name uniqueness validation before creation
        """
        pass

    @abstractmethod
    async def delete(self, bookshelf_id: UUID) -> None:
        """
        Delete a Bookshelf (soft delete via status)

        RULE-005: Changes status to DELETED
        Basement bookshelf cannot be deleted

        Args:
            bookshelf_id: UUID of the bookshelf to delete

        Raises:
            BookshelfNotFoundError: If bookshelf doesn't exist
            ValueError: If trying to delete Basement

        Design: Soft delete (status change), not hard delete
        """
        pass

    @abstractmethod
    async def exists(self, bookshelf_id: UUID) -> bool:
        """
        Check if a Bookshelf exists (any status including deleted)

        Args:
            bookshelf_id: UUID of the bookshelf

        Returns:
            True if exists (even if deleted), False otherwise
        """
        pass

    @abstractmethod
    async def find_deleted_by_library(
        self,
        library_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Bookshelf]:
        """
        Find all deleted (DELETED status) Bookshelves in a Library

        Part of Basement view - returns soft-deleted bookshelves.

        Args:
            library_id: UUID of the library
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of deleted Bookshelf domain objects
        """
        pass
