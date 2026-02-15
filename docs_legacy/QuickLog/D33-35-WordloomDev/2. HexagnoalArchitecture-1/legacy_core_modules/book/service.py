"""
Book Service

Implements 4-layer architecture for Book domain (RULE-009 through RULE-013):
  Layer 1: Validation (business rules checking)
  Layer 2: Domain Logic (core domain operations)
  Layer 3: Persistence (Repository coordination)
  Layer 4: Event Publishing (async notifications)

Supports soft delete via Basement pattern (RULE-012 & RULE-013).
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from modules.book.domain import Book, BookStatus, BookTitle, BookSummary
from modules.book.repository import BookRepository
from modules.book.exceptions import (
    BookNotFoundError,
    BookshelfNotFoundError,
    BookAlreadyExistsError,
)

logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, repository: BookRepository, bookshelf_repository=None, event_bus=None):
        self.repository = repository
        self.bookshelf_repository = bookshelf_repository  # ← For permission checks & library_id
        self.event_bus = event_bus  # ← For event publishing

    async def create_book(self, bookshelf_id: UUID, title: str, summary: str = None) -> Book:
        """
        Create a new Book with proper library_id initialization

        Layer 1: Validation - Verify Bookshelf exists
        Layer 2: Domain Logic - Book.create() with extracted library_id
        Layer 3: Persistence - Repository.save()
        Layer 4: Event Publishing - Publish BookCreated event

        Args:
            bookshelf_id: ID of the parent Bookshelf
            title: Title of the Book
            summary: Optional summary

        Returns:
            Newly created Book

        Raises:
            BookshelfNotFoundError: If Bookshelf doesn't exist
        """
        logger.info(f"Creating Book in Bookshelf {bookshelf_id} with title '{title}'")

        # ========== Layer 1: Validation ==========
        if not self.bookshelf_repository:
            logger.error("bookshelf_repository is required for create_book")
            raise Exception("bookshelf_repository is required for create_book")

        # Get Bookshelf and extract library_id (CRITICAL!)
        bookshelf = await self.bookshelf_repository.get_by_id(bookshelf_id)
        if not bookshelf:
            logger.warning(f"Bookshelf not found: {bookshelf_id}")
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")

        library_id = bookshelf.library_id
        logger.debug(f"Retrieved Library ID from Bookshelf: {library_id}")

        # ========== Layer 2: Domain Logic ==========
        # Create Book with correct library_id from Bookshelf (CRITICAL!)
        book = Book.create(
            bookshelf_id=bookshelf_id,
            library_id=library_id,  # ← MUST be initialized from Bookshelf
            title=title,
            summary=summary
        )
        logger.debug(f"Created Book domain object: {book.id}")

        # ========== Layer 3: Persistence ==========
        try:
            await self.repository.save(book)
            logger.info(f"Book persisted: {book.id}")
        except IntegrityError as e:
            logger.error(f"Integrity error persisting Book: {e}")
            raise BookAlreadyExistsError("Book already exists")
        except Exception as e:
            logger.error(f"Failed to persist Book: {e}")
            raise

        # ========== Layer 4: Event Publishing ==========
        self._publish_events(book)

        return book

    async def get_book(self, book_id: UUID) -> Book:
        """
        Retrieve Book by ID

        Args:
            book_id: Book ID

        Returns:
            Book aggregate

        Raises:
            BookNotFoundError: If not found
        """
        logger.debug(f"Retrieving Book: {book_id}")
        book = await self.repository.get_by_id(book_id)
        if not book:
            logger.warning(f"Book not found: {book_id}")
            raise BookNotFoundError(f"Book {book_id} not found")
        return book

    async def list_books(self, bookshelf_id: UUID) -> List[Book]:
        """
        List all Books in a Bookshelf

        Args:
            bookshelf_id: Parent Bookshelf ID

        Returns:
            List of Books (ordered by created_at DESC)
        """
        logger.debug(f"Listing Books in Bookshelf: {bookshelf_id}")
        books = await self.repository.get_by_bookshelf_id(bookshelf_id)
        return books

    async def rename_book(self, book_id: UUID, new_title: str) -> Book:
        """Rename Book"""
        logger.info(f"Renaming Book {book_id} to '{new_title}'")
        book = await self.get_book(book_id)

        book.rename(new_title)
        await self.repository.save(book)
        self._publish_events(book)

        return book

    async def set_summary(self, book_id: UUID, summary: Optional[str]) -> Book:
        """Set or update Book summary (Service-layer auxiliary feature)"""
        logger.info(f"Setting summary for Book {book_id}")
        book = await self.get_book(book_id)

        # Proper ValueObject creation
        if summary:
            book.summary = BookSummary(value=summary)
        else:
            book.summary = None

        book.updated_at = datetime.now(timezone.utc)
        await self.repository.save(book)
        self._publish_events(book)

        return book

    async def set_due_date(self, book_id: UUID, due_at: Optional[datetime]) -> Book:
        """Set or clear Book due date (Service-layer auxiliary feature)"""
        logger.info(f"Setting due date for Book {book_id}")
        book = await self.get_book(book_id)
        book.due_at = due_at
        book.updated_at = datetime.now(timezone.utc)
        await self.repository.save(book)
        self._publish_events(book)
        return book

    async def pin_book(self, book_id: UUID) -> Book:
        """Pin Book to top (Service-layer auxiliary feature)"""
        logger.info(f"Pinning Book {book_id}")
        book = await self.get_book(book_id)
        if not book.is_pinned:
            book.is_pinned = True
            book.updated_at = datetime.now(timezone.utc)
            await self.repository.save(book)
            self._publish_events(book)
        return book

    async def unpin_book(self, book_id: UUID) -> Book:
        """Unpin Book (Service-layer auxiliary feature)"""
        logger.info(f"Unpinning Book {book_id}")
        book = await self.get_book(book_id)
        if book.is_pinned:
            book.is_pinned = False
            book.updated_at = datetime.now(timezone.utc)
            await self.repository.save(book)
            self._publish_events(book)
        return book

    async def publish_book(self, book_id: UUID) -> Book:
        """Publish Book (change status from DRAFT to PUBLISHED)"""
        logger.info(f"Publishing Book {book_id}")
        book = await self.get_book(book_id)
        book.change_status(BookStatus.PUBLISHED)
        await self.repository.save(book)
        self._publish_events(book)
        return book

    async def archive_book(self, book_id: UUID) -> Book:
        """Archive Book (Service-layer auxiliary feature)"""
        logger.info(f"Archiving Book {book_id}")
        book = await self.get_book(book_id)
        book.change_status(BookStatus.ARCHIVED)
        await self.repository.save(book)
        self._publish_events(book)
        return book

    async def delete_book(self, book_id: UUID, basement_bookshelf_id: UUID = None) -> None:
        """
        Delete Book (soft delete - move to Basement)

        RULE-012 Implementation:
        - Does NOT hard-delete
        - Transfers Book to Basement
        - Only calls repository.save(), NOT delete()

        Args:
            book_id: Book to delete
            basement_bookshelf_id: Basement Bookshelf ID (optional if fetched from Library)

        Raises:
            BookNotFoundError: If Book not found
        """
        logger.info(f"Deleting Book (soft): {book_id}")

        # ========== Layer 1: Validation ==========
        book = await self.get_book(book_id)

        # If basement_id not provided, must fetch from Library via bookshelf_repo
        if not basement_bookshelf_id:
            if not self.bookshelf_repository:
                logger.error("bookshelf_repository required to fetch Basement")
                raise Exception("Cannot fetch Basement without bookshelf_repository")

            logger.debug(f"Fetching basement Bookshelf for Library {book.library_id}")
            bookshelf = await self.bookshelf_repository.get_basement_by_library_id(
                book.library_id
            )
            if not bookshelf:
                logger.error(f"Basement not found for Library {book.library_id}")
                raise Exception(f"Basement Bookshelf not found for Library {book.library_id}")
            basement_bookshelf_id = bookshelf.id

        # ========== Layer 2: Domain Logic ==========
        book.move_to_basement(basement_bookshelf_id)

        # ========== Layer 3: Persistence ==========
        # CRITICAL: Use save() NOT delete()!
        # RULE-012: Soft delete via move_to_basement()
        await self.repository.save(book)
        logger.info(f"Book soft-deleted: {book_id} → Basement")

        # ========== Layer 4: Event Publishing ==========
        self._publish_events(book)

    async def move_to_bookshelf(self, book_id: UUID, target_bookshelf_id: UUID) -> Book:
        """
        Move Book to different Bookshelf (with permission checks)

        Layer 1: Validation
        - Verify target Bookshelf exists
        - Verify same Library (library_id consistency)
        - Verify target is not Basement

        Layer 2: Domain Logic
        - Call book.move_to_bookshelf()

        Layer 3: Persistence
        - Save to Repository

        Args:
            book_id: Book to move
            target_bookshelf_id: Destination Bookshelf

        Returns:
            Moved Book

        Raises:
            BookNotFoundError: If Book not found
            BookshelfNotFoundError: If target not found
            PermissionError: If different Library
            ValueError: If target is Basement
        """
        logger.info(f"Moving Book {book_id} to Bookshelf {target_bookshelf_id}")

        # ========== Layer 1: Validation ==========
        book = await self.get_book(book_id)

        # Verify bookshelf_repository is available for permission checks
        if not self.bookshelf_repository:
            logger.error("bookshelf_repository is required for permission checks")
            raise Exception("bookshelf_repository is required for permission checks")

        target_shelf = await self.bookshelf_repository.get_by_id(target_bookshelf_id)
        if not target_shelf:
            logger.warning(f"Target Bookshelf not found: {target_bookshelf_id}")
            raise BookshelfNotFoundError(f"Target Bookshelf {target_bookshelf_id} not found")

        # Check same Library
        if target_shelf.library_id != book.library_id:
            logger.warning(
                f"Cross-library Book move attempted: {book.library_id} → {target_shelf.library_id}"
            )
            raise PermissionError("Cannot move Book to Bookshelf in different Library")

        # Check not Basement
        if hasattr(target_shelf, "is_basement") and target_shelf.is_basement:
            logger.warning(f"Attempted manual move to Basement: {target_bookshelf_id}")
            raise ValueError("Cannot manually move Book to Basement")

        # ========== Layer 2: Domain Logic ==========
        book.move_to_bookshelf(target_bookshelf_id)
        logger.debug(f"Book moved (domain): {book_id} → {target_bookshelf_id}")

        # ========== Layer 3: Persistence ==========
        await self.repository.save(book)
        logger.info(f"Book moved (persisted): {book_id}")

        # ========== Layer 4: Event Publishing ==========
        self._publish_events(book)

        return book

    async def move_to_basement(self, book_id: UUID, basement_bookshelf_id: UUID) -> Book:
        """Move Book to Basement (soft delete, core domain feature)"""
        logger.info(f"Moving Book to Basement: {book_id}")
        book = await self.get_book(book_id)
        book.move_to_basement(basement_bookshelf_id)
        await self.repository.save(book)
        self._publish_events(book)
        return book

    async def restore_from_basement(self, book_id: UUID, target_bookshelf_id: UUID) -> Book:
        """Restore Book from Basement (core domain feature)"""
        logger.info(f"Restoring Book from Basement: {book_id}")
        book = await self.get_book(book_id)

        if not book.is_deleted:
            logger.warning(f"Book is not deleted: {book_id}")
            raise ValueError("Book is not in Basement")

        # Verify target Bookshelf is valid
        if self.bookshelf_repository:
            target_shelf = await self.bookshelf_repository.get_by_id(target_bookshelf_id)
            if not target_shelf:
                raise BookshelfNotFoundError(f"Target Bookshelf {target_bookshelf_id} not found")

            if target_shelf.library_id != book.library_id:
                raise PermissionError("Cannot restore to Bookshelf in different Library")

            if hasattr(target_shelf, "is_basement") and target_shelf.is_basement:
                raise ValueError("Cannot restore to Basement")

        book.restore_from_basement(target_bookshelf_id)
        await self.repository.save(book)
        self._publish_events(book)
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

    # ========================================================================
    # Event Publishing
    # ========================================================================

    def _publish_events(self, book: Book) -> None:
        """
        Publish all domain events collected during operations

        Note: This is synchronous. For async event bus, override this method.
        """
        if not self.event_bus or not book.events:
            return

        for event in book.events:
            try:
                self.event_bus.publish(event)
                logger.debug(f"Published event: {event.__class__.__name__}")
            except Exception as e:
                logger.error(
                    f"Failed to publish event {event.__class__.__name__}: {e}"
                )
                # Note: We don't re-raise because Book was already persisted.
                # Consider using a dead-letter queue for failed events.

