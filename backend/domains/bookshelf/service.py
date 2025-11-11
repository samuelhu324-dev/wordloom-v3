"""
Bookshelf Service - Business logic orchestration
"""

from typing import List
from uuid import UUID

from domains.bookshelf.domain import Bookshelf, BookshelfStatus
from domains.bookshelf.repository import BookshelfRepository
from domains.bookshelf.exceptions import BookshelfNotFoundError


class BookshelfService:
    """Service for managing Bookshelf aggregate"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def create_bookshelf(
        self,
        library_id: UUID,
        name: str,
        description: str = None,
    ) -> Bookshelf:
        """Create a new Bookshelf"""
        bookshelf = Bookshelf.create(
            library_id=library_id,
            name=name,
            description=description,
        )
        await self.repository.save(bookshelf)
        return bookshelf

    async def get_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Retrieve Bookshelf by ID"""
        bookshelf = await self.repository.get_by_id(bookshelf_id)
        if not bookshelf:
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")
        return bookshelf

    async def list_bookshelves(self, library_id: UUID) -> List[Bookshelf]:
        """List all Bookshelves in a Library"""
        return await self.repository.get_by_library_id(library_id)

    async def rename_bookshelf(self, bookshelf_id: UUID, new_name: str) -> Bookshelf:
        """Rename a Bookshelf"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.rename(new_name)
        await self.repository.save(bookshelf)
        return bookshelf

    async def pin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Pin a Bookshelf"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.pin()
        await self.repository.save(bookshelf)
        return bookshelf

    async def unpin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unpin a Bookshelf"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.unpin()
        await self.repository.save(bookshelf)
        return bookshelf

    async def favorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Mark Bookshelf as favorite"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.mark_favorite()
        await self.repository.save(bookshelf)
        return bookshelf

    async def unfavorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unmark Bookshelf as favorite"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.unmark_favorite()
        await self.repository.save(bookshelf)
        return bookshelf

    async def delete_bookshelf(self, bookshelf_id: UUID) -> None:
        """Delete a Bookshelf"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.mark_deleted()
        await self.repository.save(bookshelf)
        await self.repository.delete(bookshelf_id)
