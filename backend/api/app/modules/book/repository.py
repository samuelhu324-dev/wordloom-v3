"""
Book Repository

Implements persistence layer for Book aggregate with soft-delete support.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import IntegrityError

from api.app.modules.book.domain import Book, BookTitle, BookSummary, BookStatus
from api.app.modules.book.models import BookModel
from api.app.modules.book.exceptions import BookAlreadyExistsError

logger = logging.getLogger(__name__)


class BookRepository(ABC):
    """Abstract Repository interface for Book aggregate"""

    @abstractmethod
    async def save(self, book: Book) -> None:
        """Persist or update a Book"""
        pass

    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Retrieve by ID (excluding soft-deleted)"""
        pass

    @abstractmethod
    async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]:
        """Retrieve all Books in Bookshelf (excluding soft-deleted)"""
        pass

    @abstractmethod
    async def get_deleted_books(self, bookshelf_id: UUID) -> List[Book]:
        """Retrieve soft-deleted Books (for Basement/restore)"""
        pass

    @abstractmethod
    async def delete(self, book_id: UUID) -> None:
        """Hard delete a Book"""
        pass

    @abstractmethod
    async def get_by_library_id(self, library_id: UUID) -> List[Book]:
        """Retrieve all Books in a Library (for bulk operations)"""
        pass

    @abstractmethod
    async def list_paginated(
        self,
        bookshelf_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Book], int]:
        """Retrieve paginated Books with total count"""
        pass


class BookRepositoryImpl(BookRepository):
    """SQLAlchemy implementation of BookRepository"""

    def __init__(self, session):
        self.session = session

    async def save(self, book: Book) -> None:
        """
        Save or update Book aggregate

        Handles:
        - Mapping Domain model to ORM model
        - Detecting insert vs update
        - Database constraint handling

        Raises:
            BookAlreadyExistsError: If constraint violation
        """
        try:
            # Check if model exists
            existing = await self.session.get(BookModel, book.id)

            if existing:
                # Update existing
                logger.debug(f"Updating Book: {book.id}")
                existing.bookshelf_id = book.bookshelf_id
                existing.library_id = book.library_id  # ← CRITICAL!
                existing.title = book.title.value
                existing.summary = book.summary.value if book.summary else None
                existing.is_pinned = book.is_pinned
                existing.due_at = book.due_at
                existing.status = book.status.value
                existing.block_count = book.block_count
                existing.soft_deleted_at = book.soft_deleted_at  # ← RULE-012
                existing.updated_at = book.updated_at
            else:
                # Create new
                logger.debug(f"Creating Book: {book.id}")
                model = BookModel(
                    id=book.id,
                    bookshelf_id=book.bookshelf_id,
                    library_id=book.library_id,  # ← CRITICAL!
                    title=book.title.value,
                    summary=book.summary.value if book.summary else None,
                    is_pinned=book.is_pinned,
                    due_at=book.due_at,
                    status=book.status.value,
                    block_count=book.block_count,
                    soft_deleted_at=book.soft_deleted_at,  # ← RULE-012
                    created_at=book.created_at,
                    updated_at=book.updated_at,
                )
                self.session.add(model)

        except IntegrityError as e:
            logger.error(f"Integrity constraint violated: {e}")
            error_str = str(e).lower()
            if "bookshelf_id" in error_str or "library_id" in error_str:
                raise BookAlreadyExistsError("Book already exists")
            raise

    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """
        Retrieve Book by ID (excluding soft-deleted)

        RULE-012: Automatically filters soft-deleted Books
        """
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.id == book_id,
                    BookModel.soft_deleted_at.is_(None),  # ← Exclude deleted
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                logger.debug(f"Book not found: {book_id}")
                return None

            return self._to_domain(model)

        except Exception as e:
            logger.error(f"Error fetching Book {book_id}: {e}")
            raise

    async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]:
        """
        Retrieve all Books in Bookshelf (excluding soft-deleted)

        Ordered by created_at DESC (newest first)
        """
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None),  # ← Exclude deleted
                )
            ).order_by(desc(BookModel.created_at))

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(
                f"Retrieved {len(models)} Books from Bookshelf {bookshelf_id}"
            )
            return [self._to_domain(m) for m in models]

        except Exception as e:
            logger.error(f"Error fetching Books for Bookshelf {bookshelf_id}: {e}")
            raise

    async def get_deleted_books(self, bookshelf_id: UUID) -> List[Book]:
        """
        Retrieve soft-deleted Books (for Basement/restore)

        RULE-012 & RULE-013: Supports restoring Books from Basement
        """
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_not(None),  # ← Only deleted
                )
            ).order_by(desc(BookModel.soft_deleted_at))

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(f"Retrieved {len(models)} deleted Books from {bookshelf_id}")
            return [self._to_domain(m) for m in models]

        except Exception as e:
            logger.error(f"Error fetching deleted Books: {e}")
            raise

    async def delete(self, book_id: UUID) -> None:
        """
        Hard delete a Book

        WARNING: This performs physical deletion from database.
        Use book.move_to_basement() + save() for soft delete instead.
        """
        try:
            model = await self.session.get(BookModel, book_id)
            if model:
                logger.info(f"Hard-deleting Book: {book_id}")
                await self.session.delete(model)
            else:
                logger.debug(f"Book not found for deletion: {book_id}")
        except Exception as e:
            logger.error(f"Error deleting Book {book_id}: {e}")
            raise

    def _to_domain(self, model: BookModel) -> Book:
        """
        Convert ORM model to Domain model

        Critical fields:
        - library_id: Redundant FK for permission checks
        - soft_deleted_at: For RULE-012 soft delete
        """
        return Book(
            book_id=model.id,
            bookshelf_id=model.bookshelf_id,
            library_id=model.library_id,  # ← CRITICAL!
            title=BookTitle(value=model.title),
            summary=BookSummary(value=model.summary) if model.summary else None,
            is_pinned=model.is_pinned or False,
            due_at=model.due_at,
            status=BookStatus(model.status),
            block_count=model.block_count or 0,
            soft_deleted_at=model.soft_deleted_at,  # ← RULE-012
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_library_id(self, library_id: UUID) -> List[Book]:
        """
        Retrieve all Books in a Library (excluding soft-deleted)

        Used for bulk operations and library-level queries
        """
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.library_id == library_id,
                    BookModel.soft_deleted_at.is_(None),  # ← Exclude deleted
                )
            ).order_by(desc(BookModel.created_at))

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(f"Retrieved {len(models)} Books from Library {library_id}")
            return [self._to_domain(m) for m in models]

        except Exception as e:
            logger.error(f"Error fetching Books for Library {library_id}: {e}")
            raise

    async def list_paginated(
        self,
        bookshelf_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Book], int]:
        """
        Retrieve paginated Books with total count

        Args:
            bookshelf_id: Bookshelf to query
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (books, total_count)
        """
        try:
            # Get total count
            count_stmt = select(func.count(BookModel.id)).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None),
                )
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            stmt = select(BookModel).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None),
                )
            ).order_by(desc(BookModel.created_at)).offset(offset).limit(page_size)

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(
                f"Retrieved page {page} ({len(models)} items) from Bookshelf {bookshelf_id}"
            )
            return [self._to_domain(m) for m in models], total

        except Exception as e:
            logger.error(f"Error fetching paginated Books: {e}")
            raise
