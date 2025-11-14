"""
Bookshelf Repository Implementation Adapter

Concrete SQLAlchemy implementation of BookshelfRepository output port.

Location: infra/storage/bookshelf_repository_impl.py
Port Interface: api/app/modules/bookshelf/application/ports/output.py

Architecture:
  - Implements abstract BookshelfRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces business logic: 1 Bookshelf per name per Library (RULE-006)
"""

import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from api.app.modules.bookshelf.domain import (
    Bookshelf,
    BookshelfName,
    BookshelfDescription,
    BookshelfStatus,
)
from api.app.modules.bookshelf.exceptions import BookshelfAlreadyExistsError
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from infra.database.models.bookshelf_models import BookshelfModel

logger = logging.getLogger(__name__)


class SQLAlchemyBookshelfRepository(IBookshelfRepository):
    """SQLAlchemy implementation of BookshelfRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Bookshelf domain objects to database
    - Fetch Bookshelves from database and convert to domain objects
    - Enforce unique name per Library (RULE-006)
    - Support Basement special bookshelf (RULE-010)
    - Handle transaction rollback on errors
    """

    def __init__(self, session: Session):
        """Initialize repository with database session

        Args:
            session: SQLAlchemy session for database access
        """
        self.session = session

    async def save(self, bookshelf: Bookshelf) -> None:
        """Save Bookshelf aggregate to database"""
        try:
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
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            error_str = str(e).lower()
            if "library_id" in error_str or "name" in error_str:
                logger.warning(f"Integrity constraint violated: {e}")
                raise BookshelfAlreadyExistsError(
                    "Bookshelf with this name already exists in Library"
                )
            logger.error(f"Unexpected integrity error: {e}")
            raise

    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        """Retrieve Bookshelf by ID"""
        try:
            model = self.session.query(BookshelfModel).filter(
                BookshelfModel.id == bookshelf_id
            ).first()
            if not model:
                logger.debug(f"Bookshelf not found: {bookshelf_id}")
                return None
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Bookshelf {bookshelf_id}: {e}")
            raise

    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        """Retrieve all active Bookshelves in a Library (RULE-005)"""
        try:
            models = self.session.query(BookshelfModel).filter(
                and_(
                    BookshelfModel.library_id == library_id,
                    BookshelfModel.status != "DELETED"
                )
            ).all()
            logger.debug(f"Retrieved {len(models)} Bookshelves for Library {library_id}")
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error fetching Bookshelves for Library {library_id}: {e}")
            raise

    async def get_basement_by_library_id(self, library_id: UUID) -> Optional[Bookshelf]:
        """Retrieve Basement Bookshelf for a Library (RULE-010)"""
        try:
            model = self.session.query(BookshelfModel).filter(
                and_(
                    BookshelfModel.library_id == library_id,
                    BookshelfModel.name == "Basement"
                )
            ).first()
            if not model:
                logger.debug(f"Basement not found for Library {library_id}")
                return None
            logger.debug(f"Retrieved Basement for Library {library_id}")
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Basement for Library {library_id}: {e}")
            raise

    async def exists_by_name(self, library_id: UUID, name: str) -> bool:
        """Check if Bookshelf with name exists in Library (RULE-006)"""
        try:
            exists = self.session.query(BookshelfModel).filter(
                and_(
                    BookshelfModel.library_id == library_id,
                    BookshelfModel.name == name,
                    BookshelfModel.status != "DELETED"
                )
            ).first() is not None
            logger.debug(f"Bookshelf name '{name}' exists in Library {library_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking Bookshelf name for Library {library_id}: {e}")
            raise

    async def delete(self, bookshelf_id: UUID) -> None:
        """Delete Bookshelf by ID"""
        try:
            model = self.session.query(BookshelfModel).filter(
                BookshelfModel.id == bookshelf_id
            ).first()
            if model:
                self.session.delete(model)
                self.session.commit()
                logger.info(f"Bookshelf deleted: {bookshelf_id}")
            else:
                logger.debug(f"Bookshelf not found for deletion: {bookshelf_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting Bookshelf {bookshelf_id}: {e}")
            raise

    async def exists(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf exists"""
        try:
            model = self.session.query(BookshelfModel).filter(
                BookshelfModel.id == bookshelf_id
            ).first()
            return model is not None
        except Exception as e:
            logger.error(f"Error checking Bookshelf existence {bookshelf_id}: {e}")
            raise

    def _to_domain(self, model: BookshelfModel) -> Bookshelf:
        """Convert ORM model to Domain model"""
        return Bookshelf(
            bookshelf_id=model.id,
            library_id=model.library_id,
            name=BookshelfName(value=model.name),
            description=BookshelfDescription(value=model.description) if model.description else None,
            is_pinned=model.is_pinned,
            pinned_at=model.pinned_at,
            is_favorite=model.is_favorite,
            status=BookshelfStatus(model.status),
            book_count=model.book_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
