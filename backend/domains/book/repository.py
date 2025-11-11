"""Book Repository"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domains.book.domain import Book, BookTitle, BookSummary, BookStatus
from domains.book.models import BookModel

class BookRepository(ABC):
    @abstractmethod
    async def save(self, book: Book) -> None: pass
    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]: pass
    @abstractmethod
    async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]: pass
    @abstractmethod
    async def delete(self, book_id: UUID) -> None: pass

class BookRepositoryImpl(BookRepository):
    def __init__(self, session):
        self.session = session

    async def save(self, book: Book) -> None:
        model = BookModel(
            id=book.id,
            bookshelf_id=book.bookshelf_id,
            title=book.title.value,
            summary=book.summary.value if book.summary else None,
            is_pinned=book.is_pinned,
            due_at=book.due_at,
            status=book.status.value,
            block_count=book.block_count,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
        self.session.add(model)

    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        model = await self.session.get(BookModel, book_id)
        if not model: return None
        return self._to_domain(model)

    async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]:
        from sqlalchemy import select
        stmt = select(BookModel).where(BookModel.bookshelf_id == bookshelf_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, book_id: UUID) -> None:
        model = await self.session.get(BookModel, book_id)
        if model: await self.session.delete(model)

    def _to_domain(self, model: BookModel) -> Book:
        return Book(
            book_id=model.id,
            bookshelf_id=model.bookshelf_id,
            title=BookTitle(value=model.title),
            summary=BookSummary(value=model.summary),
            is_pinned=model.is_pinned,
            due_at=model.due_at,
            status=BookStatus(model.status),
            block_count=model.block_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
