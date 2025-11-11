"""
Bookshelf Repository - Data access abstraction
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from domains.bookshelf.domain import Bookshelf
from domains.bookshelf.models import BookshelfModel


class BookshelfRepository(ABC):
    """Abstract Repository interface for Bookshelf aggregate"""

    @abstractmethod
    async def save(self, bookshelf: Bookshelf) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        pass

    @abstractmethod
    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        pass

    @abstractmethod
    async def delete(self, bookshelf_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists(self, bookshelf_id: UUID) -> bool:
        pass


class BookshelfRepositoryImpl(BookshelfRepository):
    """Concrete implementation of BookshelfRepository"""

    def __init__(self, session):
        self.session = session

    async def save(self, bookshelf: Bookshelf) -> None:
        model = BookshelfModel(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=bookshelf.name.value,
            description=bookshelf.description.value if bookshelf.description else None,
            is_pinned=bookshelf.is_pinned,
            pinned_at=bookshelf.pinned_at,
            is_favorite=bookshelf.is_favorite,
            status=bookshelf.status.value,
            book_count=bookshelf.book_count,
            created_at=bookshelf.created_at,
            updated_at=bookshelf.updated_at,
        )
        self.session.add(model)

    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        model = await self.session.get(BookshelfModel, bookshelf_id)
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        from sqlalchemy import select
        stmt = select(BookshelfModel).where(BookshelfModel.library_id == library_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, bookshelf_id: UUID) -> None:
        model = await self.session.get(BookshelfModel, bookshelf_id)
        if model:
            await self.session.delete(model)

    async def exists(self, bookshelf_id: UUID) -> bool:
        model = await self.session.get(BookshelfModel, bookshelf_id)
        return model is not None

    def _to_domain(self, model: BookshelfModel) -> Bookshelf:
        from domains.bookshelf.domain import BookshelfName, BookshelfDescription, BookshelfStatus
        return Bookshelf(
            bookshelf_id=model.id,
            library_id=model.library_id,
            name=BookshelfName(value=model.name),
            description=BookshelfDescription(value=model.description),
            is_pinned=model.is_pinned,
            pinned_at=model.pinned_at,
            is_favorite=model.is_favorite,
            status=BookshelfStatus(model.status),
            book_count=model.book_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
