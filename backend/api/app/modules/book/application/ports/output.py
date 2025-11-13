"""
Book Repository Output Port

Abstract interface for Book persistence adapter.
Implementation: infra/storage/book_repository_impl.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from api.app.modules.book.domain import Book


class BookRepository(ABC):
    """Abstract repository for Book persistence"""

    @abstractmethod
    async def save(self, book: Book) -> Book:
        """Persist a book"""
        pass

    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Fetch a book by ID"""
        pass

    @abstractmethod
    async def delete(self, book_id: UUID) -> None:
        """Delete a book"""
        pass

    @abstractmethod
    async def list_by_bookshelf(self, bookshelf_id: UUID) -> List[Book]:
        """Get all books in a bookshelf"""
        pass
