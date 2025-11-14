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
from sqlalchemy.orm import Session

from api.app.modules.book.domain import Book, BookTitle, BookSummary, BookStatus
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

    def __init__(self, session: Session):
        """Initialize repository with database session

        Args:
            session: SQLAlchemy session for database access
        """
        self.session = session

    async def save(self, book: Book) -> None:
        """Save or update Book aggregate"""
        try:
            existing = self.session.query(BookModel).filter(
                BookModel.id == book.id
            ).first()

            if existing:
                # Update existing
                logger.debug(f"Updating Book: {book.id}")
                existing.bookshelf_id = book.bookshelf_id
                existing.library_id = book.library_id
                existing.title = book.title.value
                existing.summary = book.summary.value if book.summary else None
                existing.is_pinned = book.is_pinned
                existing.due_at = book.due_at
                existing.status = book.status.value
                existing.block_count = book.block_count
                existing.soft_deleted_at = book.soft_deleted_at
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
                    is_pinned=book.is_pinned,
                    due_at=book.due_at,
                    status=book.status.value,
                    block_count=book.block_count,
                    soft_deleted_at=book.soft_deleted_at,
                    created_at=book.created_at,
                    updated_at=book.updated_at,
                )
                self.session.add(model)

            self.session.commit()

        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity constraint violated: {e}")
            error_str = str(e).lower()
            if "bookshelf_id" in error_str or "library_id" in error_str:
                raise BookAlreadyExistsError("Book already exists")
            raise

    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Retrieve Book by ID (excluding soft-deleted, RULE-012)"""
        try:
            model = self.session.query(BookModel).filter(
                and_(
                    BookModel.id == book_id,
                    BookModel.soft_deleted_at.is_(None)
                )
            ).first()

            if not model:
                logger.debug(f"Book not found: {book_id}")
                return None

            return self._to_domain(model)

        except Exception as e:
            logger.error(f"Error fetching Book {book_id}: {e}")
            raise

    async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]:
        """Retrieve all Books in Bookshelf (excluding soft-deleted)"""
        try:
            models = self.session.query(BookModel).filter(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None)
                )
            ).order_by(desc(BookModel.created_at)).all()

            logger.debug(
                f"Retrieved {len(models)} Books from Bookshelf {bookshelf_id}"
            )
            return [self._to_domain(m) for m in models]

        except Exception as e:
            logger.error(f"Error fetching Books for Bookshelf {bookshelf_id}: {e}")
            raise

    async def get_deleted_books(self, bookshelf_id: UUID) -> List[Book]:
        """Retrieve soft-deleted Books (for Basement/restore, RULE-012 & RULE-013)"""
        try:
            models = self.session.query(BookModel).filter(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.isnot(None)
                )
            ).order_by(desc(BookModel.soft_deleted_at)).all()

            logger.debug(f"Retrieved {len(models)} deleted Books from {bookshelf_id}")
            return [self._to_domain(m) for m in models]

        except Exception as e:
            logger.error(f"Error fetching deleted Books: {e}")
            raise

    async def delete(self, book_id: UUID) -> None:
        """Hard delete a Book (use soft delete in domain instead)"""
        try:
            model = self.session.query(BookModel).filter(
                BookModel.id == book_id
            ).first()
            if model:
                logger.info(f"Hard-deleting Book: {book_id}")
                self.session.delete(model)
                self.session.commit()
            else:
                logger.debug(f"Book not found for deletion: {book_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting Book {book_id}: {e}")
            raise

    async def get_by_library_id(self, library_id: UUID) -> List[Book]:
        """Retrieve all Books in a Library (excluding soft-deleted)"""
        try:
            models = self.session.query(BookModel).filter(
                and_(
                    BookModel.library_id == library_id,
                    BookModel.soft_deleted_at.is_(None)
                )
            ).order_by(desc(BookModel.created_at)).all()

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
    ) -> Tuple[List[Book], int]:
        """Retrieve paginated Books with total count"""
        try:
            # Get total count
            total = self.session.query(func.count(BookModel.id)).filter(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None),
                )
            ).scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            models = self.session.query(BookModel).filter(
                and_(
                    BookModel.bookshelf_id == bookshelf_id,
                    BookModel.soft_deleted_at.is_(None),
                )
            ).order_by(desc(BookModel.created_at)).offset(offset).limit(page_size).all()

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
            is_pinned=model.is_pinned or False,
            due_at=model.due_at,
            status=BookStatus(model.status),
            block_count=model.block_count or 0,
            soft_deleted_at=model.soft_deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def exists_by_id(self, book_id: UUID) -> bool:
        """Check if Book exists (excluding soft-deleted)"""
        try:
            exists = self.session.query(
                self.session.query(BookModel).filter(
                    and_(
                        BookModel.id == book_id,
                        BookModel.soft_deleted_at.is_(None)
                    )
                ).exists()
            ).scalar()
            return bool(exists)
        except Exception as e:
            logger.error(f"Error checking if Book exists: {e}")
            raise
