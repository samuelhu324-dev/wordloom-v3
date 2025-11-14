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
    """Abstract repository for Book persistence"""

    @abstractmethod
    async def save(self, book: Book) -> Book:
        """Persist a book (create or update)"""
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
    async def list_by_bookshelf(self, bookshelf_id: UUID) -> List[Book]:
        """Get all active books in a bookshelf (excludes soft-deleted)"""
        pass

    @abstractmethod
    async def get_deleted_books(self, bookshelf_id: UUID) -> List[Book]:
        """Get all soft-deleted books in a bookshelf (RULE-012/013: Basement view)"""
        pass

    @abstractmethod
    async def list_paginated(
        self, bookshelf_id: UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Book], int]:
        """Get paginated active books with total count (for pagination support)"""
        pass

    @abstractmethod
    async def get_by_library_id(self, library_id: UUID) -> List[Book]:
        """Get all active books in a library (cross-bookshelf query for RULE-011)"""
        pass

    @abstractmethod
    async def exists_by_id(self, book_id: UUID) -> bool:
        """Check if book exists (for permission validation optimization)"""
        pass
