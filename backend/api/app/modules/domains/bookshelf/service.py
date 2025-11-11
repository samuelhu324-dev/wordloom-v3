"""
Bookshelf Service - Business logic orchestration
"""

from datetime import datetime
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

    async def set_description(self, bookshelf_id: UUID, description: str = None) -> Bookshelf:
        """Set or update Bookshelf description (Service-layer metadata operation)"""
        from domains.bookshelf.domain import BookshelfDescription
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.description = BookshelfDescription(value=description)
        bookshelf.updated_at = datetime.utcnow()
        await self.repository.save(bookshelf)
        return bookshelf

    async def pin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Pin a Bookshelf to top (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        if not bookshelf.is_pinned:
            bookshelf.is_pinned = True
            bookshelf.pinned_at = datetime.utcnow()
            bookshelf.updated_at = bookshelf.pinned_at
            await self.repository.save(bookshelf)
        return bookshelf

    async def unpin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unpin a Bookshelf (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        if bookshelf.is_pinned:
            bookshelf.is_pinned = False
            bookshelf.pinned_at = None
            bookshelf.updated_at = datetime.utcnow()
            await self.repository.save(bookshelf)
        return bookshelf

    async def favorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Mark Bookshelf as favorite (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        if not bookshelf.is_favorite:
            bookshelf.is_favorite = True
            bookshelf.updated_at = datetime.utcnow()
            await self.repository.save(bookshelf)
        return bookshelf

    async def unfavorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unmark Bookshelf as favorite (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        if bookshelf.is_favorite:
            bookshelf.is_favorite = False
            bookshelf.updated_at = datetime.utcnow()
            await self.repository.save(bookshelf)
        return bookshelf

    async def archive_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Archive a Bookshelf (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.change_status(BookshelfStatus.ARCHIVED)
        await self.repository.save(bookshelf)
        return bookshelf

    async def unarchive_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unarchive a Bookshelf (Service-layer auxiliary feature)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.change_status(BookshelfStatus.ACTIVE)
        await self.repository.save(bookshelf)
        return bookshelf

    async def delete_bookshelf(self, bookshelf_id: UUID) -> None:
        """Delete a Bookshelf (soft delete via Basement pattern)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.mark_deleted()
        await self.repository.save(bookshelf)
        await self.repository.delete(bookshelf_id)

    # ========================================================================
    # Query Methods (Moved from Domain)
    # ========================================================================

    async def can_accept_books(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf can accept new Books (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status != BookshelfStatus.DELETED

    async def is_active(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is active (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.ACTIVE

    async def is_archived(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is archived (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.ARCHIVED

    async def is_deleted(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is deleted (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.DELETED
