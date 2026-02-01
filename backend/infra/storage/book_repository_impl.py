"""
Book Repository Implementation Adapter

Concrete SQLAlchemy implementation of BookRepository output port.

Location: infra/storage/book_repository_impl.py
Port Interface: api/app/modules/book/application/ports/output.py

Architecture:
  - Implements abstract BookRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces soft-delete logic (RULE-012)
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.book.domain import Book, BookTitle, BookSummary, BookStatus, BookMaturity
from api.app.modules.book.exceptions import BookAlreadyExistsError
from api.app.modules.book.application.ports.output import BookRepository
from infra.database.models import BookModel

logger = logging.getLogger(__name__)


class SQLAlchemyBookRepository(BookRepository):
    """SQLAlchemy implementation of BookRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Book domain objects to database
    - Fetch Books from database and convert to domain objects
    - Enforce soft-delete logic (RULE-012: soft_deleted_at field)
    - Support pagination for UI list views
    - Handle transaction rollback on errors
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session

        Args:
            session: AsyncSession for async database access
        """
        self.session = session

    async def save(self, book: Book) -> Book:
        """Save or update Book aggregate and return Domain object.

        Commit/rollback is handled by the outer Unit of Work / request boundary.
        """
        try:
            stmt = select(BookModel).where(BookModel.id == book.id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                logger.debug(f"Updating Book: {book.id}")
                existing.bookshelf_id = book.bookshelf_id
                existing.library_id = book.library_id
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
                existing.soft_deleted_at = book.soft_deleted_at
                existing.previous_bookshelf_id = getattr(book, "previous_bookshelf_id", None)
                existing.moved_to_basement_at = getattr(book, "moved_to_basement_at", None)
                existing.updated_at = book.updated_at
            else:
                # Create new
                logger.debug(f"Creating Book: {book.id}")
                model = BookModel(
                    id=book.id,
                    bookshelf_id=book.bookshelf_id,
                    library_id=book.library_id,
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
                    soft_deleted_at=book.soft_deleted_at,
                    previous_bookshelf_id=getattr(book, "previous_bookshelf_id", None),
                    moved_to_basement_at=getattr(book, "moved_to_basement_at", None),
                    created_at=book.created_at,
                    updated_at=book.updated_at,
                )
                self.session.add(model)

            await self.session.flush()
            return book

        except IntegrityError as e:
            logger.error(f"Integrity constraint violated: {e}")
            error_str = str(e).lower()
            if "bookshelf_id" in error_str or "library_id" in error_str:
                raise BookAlreadyExistsError("Book already exists")
            raise

    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Retrieve Book by ID (excluding soft-deleted, RULE-012)"""
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.id == book_id,
                    BookModel.soft_deleted_at.is_(None)
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
        include_deleted: bool = False
    ) -> Tuple[List[Book], int]:
        """Retrieve Books in Bookshelf with pagination

        Args:
            bookshelf_id: Bookshelf ID to filter by
            skip: Pagination offset
            limit: Pagination limit
            include_deleted: Include soft-deleted books (default False, RULE-012)

        Returns:
            Tuple of (list of Book objects, total count)
        """
        try:
            filters = [BookModel.bookshelf_id == bookshelf_id]
            if not include_deleted:
                filters.append(BookModel.soft_deleted_at.is_(None))

            # Get total count
            count_stmt = select(func.count(BookModel.id)).where(and_(*filters))
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Get paginated results
            stmt = (
                select(BookModel)
                .where(and_(*filters))
                .order_by(desc(BookModel.created_at))
                .offset(skip)
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(
                f"Retrieved {len(models)} Books from Bookshelf {bookshelf_id} (skip={skip}, limit={limit}, total={total})"
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
    ) -> Tuple[List[Book], int]:
        """Retrieve soft-deleted Books with optional filters & pagination.

        Supports Basement view (RULE-012/013) used by list_deleted_books use case.
        Returns (items, total_count).
        """
        try:
            filters = [BookModel.soft_deleted_at.isnot(None)]
            if bookshelf_id:
                filters.append(BookModel.bookshelf_id == bookshelf_id)
            if library_id:
                filters.append(BookModel.library_id == library_id)
            if book_id:
                filters.append(BookModel.id == book_id)

            count_stmt = select(func.count(BookModel.id)).where(and_(*filters))
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            stmt = (
                select(BookModel)
                .where(and_(*filters))
                .order_by(desc(BookModel.soft_deleted_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(
                f"Retrieved {len(models)} deleted Books (skip={skip}, limit={limit}, total={total}, "
                f"bookshelf_id={bookshelf_id}, library_id={library_id})"
            )
            return [self._to_domain(m) for m in models], total
        except Exception as e:
            logger.error(f"Error fetching deleted Books: {e}")
            raise


    async def delete(self, book_id: UUID) -> None:
        """Hard delete a Book (use soft delete in domain instead)"""
        try:
            stmt = select(BookModel).where(BookModel.id == book_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if model:
                logger.info(f"Hard-deleting Book: {book_id}")
                await self.session.delete(model)
                await self.session.commit()
            else:
                logger.debug(f"Book not found for deletion: {book_id}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting Book {book_id}: {e}")
            raise

    async def get_by_library_id(
        self,
        library_id: Optional[UUID],
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False
    ) -> Tuple[List[Book], int]:
        """Retrieve Books in a Library with pagination

        Args:
            library_id: Library ID to filter by (optional)
            skip: Pagination offset
            limit: Pagination limit
            include_deleted: Include soft-deleted books (default False, RULE-012)

        Returns:
            Tuple of (list of Book objects, total count)
        """
        try:
            if not library_id:
                return [], 0

            filters = [BookModel.library_id == library_id]
            if not include_deleted:
                filters.append(BookModel.soft_deleted_at.is_(None))

            # Get total count
            count_stmt = select(func.count(BookModel.id)).where(and_(*filters))
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Get paginated results
            stmt = (
                select(BookModel)
                .where(and_(*filters))
                .order_by(desc(BookModel.created_at))
                .offset(skip)
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            logger.debug(f"Retrieved {len(models)} Books from Library {library_id} (skip={skip}, limit={limit}, total={total})")
            return [self._to_domain(m) for m in models], total

        except Exception as e:
            logger.error(f"Error fetching Books for Library {library_id}: {e}")
            raise

    async def list_paginated(
        self,
        bookshelf_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Book], int]:
        """Retrieve paginated Books with total count"""
        try:
            # Get total count using async query
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

    def _to_domain(self, model: BookModel) -> Book:
        """Convert ORM model to Domain model"""
        return Book(
            book_id=model.id,
            bookshelf_id=model.bookshelf_id,
            library_id=model.library_id,
            title=BookTitle(value=model.title),
            summary=BookSummary(value=model.summary) if model.summary else None,
            cover_icon=model.cover_icon,
            cover_media_id=model.cover_media_id,
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
            soft_deleted_at=model.soft_deleted_at,
            previous_bookshelf_id=getattr(model, "previous_bookshelf_id", None),
            moved_to_basement_at=getattr(model, "moved_to_basement_at", None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_content_edit_at=getattr(model, "last_content_edit_at", None),
        )

    async def exists_by_id(self, book_id: UUID) -> bool:
        """Check if Book exists (excluding soft-deleted)"""
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.id == book_id,
                    BookModel.soft_deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return model is not None
        except Exception as e:
            logger.error(f"Error checking if Book exists: {e}")
            raise

    async def list_by_bookshelf(
        self,
        bookshelf_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List['Book']:
        """List all Books in a Bookshelf (excluding soft-deleted)"""
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None)
                )
            ).limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._to_domain(model) for model in models]
        except Exception as e:
            logger.error(f"Error listing books for bookshelf {bookshelf_id}: {e}")
            raise
