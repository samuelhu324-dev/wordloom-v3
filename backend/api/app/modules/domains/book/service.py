"""Book Service"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from domains.book.domain import Book, BookStatus
from domains.book.repository import BookRepository


class BookService:
    def __init__(self, repository: BookRepository, bookshelf_repository = None):
        self.repository = repository
        self.bookshelf_repository = bookshelf_repository  # ← For permission checks

    async def create_book(self, bookshelf_id: UUID, title: str, summary: str = None) -> Book:
        """
        Create a new Book with proper library_id initialization

        Args:
            bookshelf_id: ID of the parent Bookshelf
            title: Title of the Book
            summary: Optional summary

        Returns:
            Newly created Book

        Raises:
            BookshelfNotFoundError: If Bookshelf doesn't exist
        """
        # Step 1: Get Bookshelf and extract library_id
        bookshelf = await self.repository.get_by_bookshelf_id(bookshelf_id)
        if not bookshelf:
            raise Exception(f"Bookshelf {bookshelf_id} not found")

        # Step 2: Create Book with correct library_id
        book = Book.create(
            bookshelf_id=bookshelf_id,
            library_id=bookshelf.library_id,  # ← Properly initialized from Bookshelf
            title=title,
            summary=summary
        )

        # Step 3: Persist
        await self.repository.save(book)
        return book

    async def get_book(self, book_id: UUID) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise Exception(f"Book {book_id} not found")
        return book

    async def list_books(self, bookshelf_id: UUID) -> List[Book]:
        return await self.repository.get_by_bookshelf_id(bookshelf_id)

    async def rename_book(self, book_id: UUID, new_title: str) -> Book:
        book = await self.get_book(book_id)
        book.rename(new_title)
        await self.repository.save(book)
        return book

    async def set_summary(self, book_id: UUID, summary: Optional[str]) -> Book:
        """Set or update Book summary (Service-layer auxiliary feature, moved from Domain)"""
        book = await self.get_book(book_id)
        book.summary = book.summary.__class__(value=summary)  # ← Update via ValueObject
        book.updated_at = datetime.utcnow()
        await self.repository.save(book)
        return book

    async def set_due_date(self, book_id: UUID, due_at: Optional[datetime]) -> Book:
        """Set or clear Book due date (Service-layer auxiliary feature)"""
        book = await self.get_book(book_id)
        book.due_at = due_at
        book.updated_at = datetime.utcnow()
        await self.repository.save(book)
        return book

    async def pin_book(self, book_id: UUID) -> Book:
        """Pin Book to top (Service-layer auxiliary feature)"""
        book = await self.get_book(book_id)
        if not book.is_pinned:
            book.is_pinned = True
            book.updated_at = datetime.utcnow()
            await self.repository.save(book)
        return book

    async def unpin_book(self, book_id: UUID) -> Book:
        """Unpin Book (Service-layer auxiliary feature)"""
        book = await self.get_book(book_id)
        if book.is_pinned:
            book.is_pinned = False
            book.updated_at = datetime.utcnow()
            await self.repository.save(book)
        return book

    async def publish_book(self, book_id: UUID) -> Book:
        """Publish Book (change status from DRAFT to PUBLISHED)"""
        book = await self.get_book(book_id)
        book.change_status(BookStatus.PUBLISHED)
        await self.repository.save(book)
        return book

    async def archive_book(self, book_id: UUID) -> Book:
        """Archive Book (Service-layer auxiliary feature)"""
        book = await self.get_book(book_id)
        book.change_status(BookStatus.ARCHIVED)
        await self.repository.save(book)
        return book

    async def delete_book(self, book_id: UUID, basement_bookshelf_id: UUID) -> None:
        """Delete Book (soft delete - move to Basement)"""
        book = await self.get_book(book_id)
        book.move_to_basement(basement_bookshelf_id)  # ← Soft delete
        await self.repository.save(book)  # ← Only persist, don't hard delete

    async def move_to_bookshelf(self, book_id: UUID, target_bookshelf_id: UUID) -> Book:
        """Move Book to different Bookshelf (with permission checks)"""
        # Step 1: Get Book
        book = await self.get_book(book_id)

        # Step 2: Verify target Bookshelf exists (if bookshelf_repository available)
        if self.bookshelf_repository:
            target_shelf = await self.bookshelf_repository.get_by_id(target_bookshelf_id)
            if not target_shelf:
                raise Exception(f"Target Bookshelf {target_bookshelf_id} not found")

            # Step 3: Verify both Bookshelves belong to the same Library
            if target_shelf.library_id != book.library_id:
                raise PermissionError("Cannot move Book to Bookshelf in different Library")

            # Step 4: Verify target is not Basement
            if hasattr(target_shelf, 'is_basement') and target_shelf.is_basement:
                raise ValueError("Cannot manually move Book to Basement")

        # Step 5: Execute move
        book.move_to_bookshelf(target_bookshelf_id)
        await self.repository.save(book)
        return book

    async def move_to_basement(self, book_id: UUID, basement_bookshelf_id: UUID) -> Book:
        """Move Book to Basement (soft delete, core domain feature)"""
        book = await self.get_book(book_id)
        book.move_to_basement(basement_bookshelf_id)
        await self.repository.save(book)
        return book

    async def restore_from_basement(self, book_id: UUID, target_bookshelf_id: UUID) -> Book:
        """Restore Book from Basement (core domain feature)"""
        book = await self.get_book(book_id)
        book.restore_from_basement(target_bookshelf_id)
        await self.repository.save(book)
        return book

    # ========================================================================
    # Query Methods (Moved from Domain)
    # ========================================================================

    async def is_draft(self, book_id: UUID) -> bool:
        """Check if Book is in draft status"""
        book = await self.get_book(book_id)
        return book.is_draft

    async def is_published(self, book_id: UUID) -> bool:
        """Check if Book is published"""
        book = await self.get_book(book_id)
        return book.is_published

    async def is_archived(self, book_id: UUID) -> bool:
        """Check if Book is archived"""
        book = await self.get_book(book_id)
        return book.is_archived

    async def is_deleted(self, book_id: UUID) -> bool:
        """Check if Book is deleted"""
        book = await self.get_book(book_id)
        return book.is_deleted

    async def can_edit(self, book_id: UUID) -> bool:
        """Check if Book can be edited"""
        book = await self.get_book(book_id)
        return book.can_edit

