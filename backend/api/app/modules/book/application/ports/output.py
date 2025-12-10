"""
Book Repository Output Port

Abstract interface for Book persistence adapter.
Implementation: infra/storage/book_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ...domain import Book


class BookRepository(ABC):
    """Abstract repository for Book persistence.

    All mutating operations return the Domain Book when applicable for
    fluent use in use cases (e.g., create → return created aggregate).
    """

    @abstractmethod
    async def save(self, book: Book) -> Book:
        """Persist a book (create or update) and return Domain aggregate"""
        pass

    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Fetch a book by ID (auto-filters soft-deleted)"""
        pass

    @abstractmethod
    async def delete(self, book_id: UUID) -> None:
        """Hard delete a book (should not be used in normal flow)"""
        pass

    @abstractmethod
    async def get_by_bookshelf_id(
        self,
        bookshelf_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False
    ) -> Tuple[List[Book], int]:
        """Get books in a bookshelf with pagination

        Args:
            bookshelf_id: Bookshelf ID to filter by
            skip: Pagination offset
            limit: Pagination limit
            include_deleted: Include soft-deleted books (default False, RULE-012)

        Returns:
            Tuple of (list of Book objects, total count)
        """
        pass

    @abstractmethod
    async def get_by_library_id(
        self,
        library_id: Optional[UUID],
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False
    ) -> Tuple[List[Book], int]:
        """Get books in a library with pagination

        Args:
            library_id: Library ID to filter by (optional)
            skip: Pagination offset
            limit: Pagination limit
            include_deleted: Include soft-deleted books (default False, RULE-012)

        Returns:
            Tuple of (list of Book objects, total count)
        """
        pass

    @abstractmethod
    async def list_by_bookshelf(self, bookshelf_id: UUID) -> List[Book]:
        """Get all active books in a bookshelf (excludes soft-deleted)"""
        pass

    @abstractmethod
    async def get_deleted_books(
        self,
        skip: int = 0,
        limit: int = 50,
        bookshelf_id: Optional[UUID] = None,
        library_id: Optional[UUID] = None,
        book_id: Optional[UUID] = None,
    ) -> Tuple[List[Book], int]:
        """Get soft-deleted books with optional filters & pagination.

        Returns (items, total_count).
        Compatible with Basement stats derivation (RULE-012/013).
        """
        pass

    @abstractmethod
    async def list_paginated(
        self, bookshelf_id: UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Book], int]:
        """Get paginated active books with total count (for pagination support)"""
        pass

    @abstractmethod
    async def exists_by_id(self, book_id: UUID) -> bool:
        """Check if book exists (for permission validation optimization)"""
        pass
