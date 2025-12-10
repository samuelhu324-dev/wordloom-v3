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

from api.app.modules.book.domain import Book, BookTitle, BookSummary, BookStatus, BookMaturity
from api.app.modules.book.models import BookModel
from api.app.modules.book.exceptions import BookAlreadyExistsError

logger = logging.getLogger(__name__)


class BookRepository(ABC):
    """Abstract Repository interface for Book aggregate (mirrors output port)

    NOTE: save returns the Domain Book for fluent usage in use cases.
    """

    @abstractmethod
    async def save(self, book: Book) -> Book:
        pass

    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        pass

    @abstractmethod
    async def get_by_bookshelf_id(
        self,
        bookshelf_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[List[Book], int]:
        pass

    @abstractmethod
    async def get_by_library_id(
        self,
        library_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[List[Book], int]:
        pass

    @abstractmethod
    async def list_paginated(
        self,
        bookshelf_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Book], int]:
        pass

    @abstractmethod
    async def get_deleted_books(
        self,
        skip: int = 0,
        limit: int = 50,
        bookshelf_id: Optional[UUID] = None,
        library_id: Optional[UUID] = None,
    ) -> tuple[List[Book], int]:
        pass

    @abstractmethod
    async def delete(self, book_id: UUID) -> None:
        pass

    @abstractmethod
    async def exists_by_id(self, book_id: UUID) -> bool:
        pass


class BookRepositoryImpl(BookRepository):
    """SQLAlchemy implementation of BookRepository"""

    def __init__(self, session):
        self.session = session

    async def save(self, book: Book) -> Book:
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
                existing.cover_icon = book.cover_icon
                existing.cover_media_id = book.cover_media_id
                existing.is_pinned = book.is_pinned
                existing.due_at = book.due_at
                existing.status = book.status.value
                existing.maturity = book.maturity.value
                existing.maturity_score = getattr(book, "maturity_score", 0)
                existing.legacy_flag = getattr(book, "legacy_flag", False)
                existing.manual_maturity_override = getattr(book, "manual_maturity_override", False)
                existing.manual_maturity_reason = getattr(book, "manual_maturity_reason", None)
                existing.last_visited_at = getattr(book, "last_visited_at", None)
                existing.visit_count_90d = getattr(book, "visit_count_90d", 0)
                existing.block_count = book.block_count
                existing.soft_deleted_at = book.soft_deleted_at  # ← RULE-012
                existing.previous_bookshelf_id = getattr(book, "previous_bookshelf_id", None)
                existing.moved_to_basement_at = getattr(book, "moved_to_basement_at", None)
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
                    cover_icon=book.cover_icon,
                    cover_media_id=book.cover_media_id,
                    is_pinned=book.is_pinned,
                    due_at=book.due_at,
                    status=book.status.value,
                    maturity=book.maturity.value,
                    maturity_score=getattr(book, "maturity_score", 0),
                    legacy_flag=getattr(book, "legacy_flag", False),
                    manual_maturity_override=getattr(book, "manual_maturity_override", False),
                    manual_maturity_reason=getattr(book, "manual_maturity_reason", None),
                    last_visited_at=getattr(book, "last_visited_at", None),
                    visit_count_90d=getattr(book, "visit_count_90d", 0),
                    block_count=book.block_count,
                    soft_deleted_at=book.soft_deleted_at,  # ← RULE-012
                    previous_bookshelf_id=getattr(book, "previous_bookshelf_id", None),
                    moved_to_basement_at=getattr(book, "moved_to_basement_at", None),
                    created_at=book.created_at,
                    updated_at=book.updated_at,
                )
                self.session.add(model)

            # Flush to persist (without committing here; Unit of Work may handle commit)
            try:
                await self.session.flush()
            except Exception as flush_err:
                logger.warning(f"Flush after save failed (non-fatal before commit): {flush_err}")

            return book

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

    async def get_by_bookshelf_id(
        self,
        bookshelf_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[List[Book], int]:
        """Retrieve books in a bookshelf with pagination & optional deleted inclusion"""
        try:
            # Total count (respect deleted filter)
            total_stmt = select(func.count(BookModel.id)).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    (BookModel.soft_deleted_at.is_(None) if not include_deleted else True),
                )
            )
            total_result = await self.session.execute(total_stmt)
            total = total_result.scalar() or 0

            # Items query
            where_clause = and_(
                BookModel.bookshelf_id == bookshelf_id,
                (BookModel.soft_deleted_at.is_(None) if not include_deleted else True),
            )
            stmt = (
                select(BookModel)
                .where(where_clause)
                .order_by(desc(BookModel.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            logger.debug(
                f"Retrieved {len(models)} Books (total={total}) from Bookshelf {bookshelf_id} include_deleted={include_deleted}"
            )
            return [self._to_domain(m) for m in models], total
        except Exception as e:
            logger.error(f"Error fetching Books for Bookshelf {bookshelf_id}: {e}")
            raise

    async def get_deleted_books(
        self,
        skip: int = 0,
        limit: int = 50,
        bookshelf_id: Optional[UUID] = None,
        library_id: Optional[UUID] = None,
        book_id: Optional[UUID] = None,
    ) -> tuple[List[Book], int]:
        """Retrieve soft-deleted books with optional filters"""
        try:
            conditions = [BookModel.soft_deleted_at.is_not(None)]
            if bookshelf_id:
                conditions.append(BookModel.bookshelf_id == bookshelf_id)
            if library_id:
                conditions.append(BookModel.library_id == library_id)
            if book_id:
                conditions.append(BookModel.id == book_id)

            total_stmt = select(func.count(BookModel.id)).where(and_(*conditions))
            total_result = await self.session.execute(total_stmt)
            total = total_result.scalar() or 0

            stmt = (
                select(BookModel)
                .where(and_(*conditions))
                .order_by(desc(BookModel.soft_deleted_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            logger.debug(
                f"Retrieved {len(models)} deleted Books (total={total}) filters bookshelf={bookshelf_id} library={library_id}"
            )
            return [self._to_domain(m) for m in models], total
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
                await self.session.flush()
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
            cover_icon=model.cover_icon,
            cover_media_id=getattr(model, "cover_media_id", None),
            is_pinned=model.is_pinned or False,
            due_at=model.due_at,
            status=BookStatus(model.status),
            maturity=BookMaturity(model.maturity),
            maturity_score=model.maturity_score or 0,
            legacy_flag=model.legacy_flag or False,
            manual_maturity_override=model.manual_maturity_override or False,
            manual_maturity_reason=model.manual_maturity_reason,
            last_visited_at=model.last_visited_at,
            visit_count_90d=model.visit_count_90d or 0,
            block_count=model.block_count or 0,
            block_type_count=getattr(model, "block_type_count", 0) or 0,
            tag_count_snapshot=getattr(model, "tag_count_snapshot", 0) or 0,
            open_todo_snapshot=getattr(model, "open_todo_snapshot", 0) or 0,
            operations_bonus=getattr(model, "operations_bonus", 0) or 0,
            soft_deleted_at=model.soft_deleted_at,  # ← RULE-012
            previous_bookshelf_id=getattr(model, "previous_bookshelf_id", None),
            moved_to_basement_at=getattr(model, "moved_to_basement_at", None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_content_edit_at=getattr(model, "last_content_edit_at", None),
        )

    async def get_by_library_id(
        self,
        library_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[List[Book], int]:
        """Retrieve books in a library with pagination & optional deleted inclusion"""
        try:
            total_stmt = select(func.count(BookModel.id)).where(
                and_(
                    BookModel.library_id == library_id,
                    (BookModel.soft_deleted_at.is_(None) if not include_deleted else True),
                )
            )
            total_result = await self.session.execute(total_stmt)
            total = total_result.scalar() or 0

            where_clause = and_(
                BookModel.library_id == library_id,
                (BookModel.soft_deleted_at.is_(None) if not include_deleted else True),
            )
            stmt = (
                select(BookModel)
                .where(where_clause)
                .order_by(desc(BookModel.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            logger.debug(
                f"Retrieved {len(models)} Books (total={total}) from Library {library_id} include_deleted={include_deleted}"
            )
            return [self._to_domain(m) for m in models], total
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

    async def exists_by_id(self, book_id: UUID) -> bool:
        """Check if a Book exists (any status)"""
        try:
            stmt = select(func.count(BookModel.id)).where(BookModel.id == book_id)
            result = await self.session.execute(stmt)
            return (result.scalar() or 0) > 0
        except Exception as e:
            logger.error(f"Error checking existence for Book {book_id}: {e}")
            return False
