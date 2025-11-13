"""
Library Repository Implementation Adapter

Concrete SQLAlchemy implementation of LibraryRepository output port.

Location: infra/storage/library_repository_impl.py
Port Interface: api/app/modules/library/application/ports/output.py

Architecture:
  - Implements abstract LibraryRepository interface (output port)
  - Uses SQLAlchemy ORM models from infra/database/models
  - Converts ORM models ↔ Domain objects
  - Manages database transactions and error handling
  - Enforces business logic: 1 Library per user (RULE-001)
"""

import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.modules.library.domain import Library, LibraryName
from api.app.modules.library.exceptions import LibraryAlreadyExistsError
from api.app.modules.library.application.ports.output import LibraryRepository
from infra.database.models import LibraryModel

logger = logging.getLogger(__name__)


class SQLAlchemyLibraryRepository(LibraryRepository):
    """SQLAlchemy implementation of LibraryRepository (Infrastructure Adapter)

    This is an ADAPTER in Hexagonal architecture - it implements the
    output port interface defined in application/ports/output.py.

    Responsibilities:
    - Persist Library domain objects to database
    - Fetch Libraries from database and convert to domain objects
    - Enforce 1 Library per user (RULE-001)
    - Handle transaction rollback on errors
    """

    def __init__(self, session: Session):
        """Initialize repository with database session

        Args:
            session: SQLAlchemy session for database access
        """
        self.session = session

    async def save(self, library: Library) -> None:
        """Save Library aggregate to database"""
        try:
            model = LibraryModel(
                id=library.id,
                user_id=library.user_id,
                name=library.name.value,
                created_at=library.created_at,
                updated_at=library.updated_at,
            )
            self.session.add(model)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            error_str = str(e).lower()
            if "user_id" in error_str or "unique" in error_str:
                logger.warning(f"Integrity constraint violated: {e}")
                raise LibraryAlreadyExistsError(
                    "User already has a Library (database constraint)"
                )
            logger.error(f"Unexpected integrity error: {e}")
            raise

    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """Retrieve Library by ID"""
        try:
            model = self.session.query(LibraryModel).filter(
                LibraryModel.id == library_id
            ).first()
            if not model:
                logger.debug(f"Library not found: {library_id}")
                return None
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Library {library_id}: {e}")
            raise

    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """Retrieve Library by user ID (unique: 1 Library per user)"""
        try:
            models = self.session.query(LibraryModel).filter(
                LibraryModel.user_id == user_id
            ).all()

            if not models:
                logger.debug(f"No Library found for user: {user_id}")
                return None

            if len(models) > 1:
                logger.error(
                    f"RULE-001 violation: User {user_id} has {len(models)} Libraries! "
                    f"Returning first one, but this indicates data corruption."
                )

            model = models[0]
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Library for user {user_id}: {e}")
            raise

    async def delete(self, library_id: UUID) -> None:
        """Delete Library by ID"""
        try:
            model = self.session.query(LibraryModel).filter(
                LibraryModel.id == library_id
            ).first()
            if model:
                self.session.delete(model)
                self.session.commit()
                logger.info(f"Library deleted: {library_id}")
            else:
                logger.debug(f"Library not found for deletion: {library_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting Library {library_id}: {e}")
            raise

    async def exists(self, library_id: UUID) -> bool:
        """Check if Library exists"""
        try:
            model = self.session.query(LibraryModel).filter(
                LibraryModel.id == library_id
            ).first()
            return model is not None
        except Exception as e:
            logger.error(f"Error checking Library existence {library_id}: {e}")
            raise

    def _to_domain(self, model: LibraryModel) -> Library:
        """Convert ORM model to Domain model"""
        return Library(
            library_id=model.id,
            user_id=model.user_id,
            name=LibraryName(value=model.name),
            basement_bookshelf_id=getattr(model, 'basement_bookshelf_id', None),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
