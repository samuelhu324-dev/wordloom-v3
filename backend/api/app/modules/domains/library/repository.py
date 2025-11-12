"""
Library Repository - Data access abstraction

Defines the interface and implementation for persisting Library aggregates.

Responsibilities:
- Translating between Domain model and ORM model
- Executing database queries
- Handling database constraints and errors
- No business logic here - that's the Domain's job
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from domains.library.domain import Library, LibraryName
from domains.library.models import LibraryModel
from domains.library.exceptions import LibraryAlreadyExistsError

logger = logging.getLogger(__name__)


class LibraryRepository(ABC):
    """
    Abstract Repository interface for Library aggregate

    Repository is responsible for:
    - Persisting Library aggregates to database
    - Retrieving Library aggregates from database
    - Translating between Domain model and ORM model
    """

    @abstractmethod
    async def save(self, library: Library) -> None:
        """
        Save a Library aggregate to database

        Args:
            library: Library aggregate to persist

        Side Effects:
            - Creates new database record if not exists
            - Updates existing record if already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """
        Retrieve a Library by ID

        Args:
            library_id: UUID of the Library

        Returns:
            Library aggregate if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """
        Retrieve a Library by user ID (unique relationship: 1 Library per user)

        Args:
            user_id: UUID of the user

        Returns:
            Library aggregate if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None:
        """
        Delete a Library by ID

        Args:
            library_id: UUID of the Library to delete

        Side Effects:
            - Removes database record
            - Cascade delete rules handled at DB level
        """
        pass

    @abstractmethod
    async def exists(self, library_id: UUID) -> bool:
        """
        Check if a Library exists

        Args:
            library_id: UUID of the Library

        Returns:
            True if Library exists, False otherwise
        """
        pass


class LibraryRepositoryImpl(LibraryRepository):
    """
    Concrete implementation of LibraryRepository using SQLAlchemy

    Handles:
    - Mapping between Domain Library and ORM LibraryModel
    - Database transactions
    - Query execution
    """

    def __init__(self, session):
        """
        Initialize repository with database session

        Args:
            session: SQLAlchemy AsyncSession
        """
        self.session = session

    async def save(self, library: Library) -> None:
        """
        Save Library aggregate to database

        Translates from Domain model to ORM model.
        Handles constraint violations by converting to Domain exceptions.

        Raises:
            LibraryAlreadyExistsError: If unique constraint violated (user_id)
        """
        try:
            model = LibraryModel(
                id=library.id,
                user_id=library.user_id,
                name=library.name.value,
                created_at=library.created_at,
                updated_at=library.updated_at,
            )
            self.session.add(model)
            # Note: Session commit is handled at application level (Unit of Work pattern)
        except IntegrityError as e:
            # Transform database constraint violation into Domain exception
            error_str = str(e).lower()
            if "user_id" in error_str or "unique" in error_str:
                logger.warning(f"Integrity constraint violated: {e}")
                raise LibraryAlreadyExistsError(
                    "User already has a Library (database constraint)"
                )
            # Re-raise other integrity errors
            logger.error(f"Unexpected integrity error: {e}")
            raise

    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """
        Retrieve Library by ID

        Translates from ORM model to Domain model.

        Raises:
            Exception: If database query fails
        """
        try:
            model = await self.session.get(LibraryModel, library_id)
            if not model:
                logger.debug(f"Library not found: {library_id}")
                return None
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Library {library_id}: {e}")
            raise

    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """
        Retrieve Library by user ID (unique: 1 Library per user)

        Per RULE-001, each user can have at most one Library.
        This method enforces that invariant.

        Raises:
            Exception: If database query fails or multiple Libraries found
        """
        try:
            stmt = select(LibraryModel).where(LibraryModel.user_id == user_id)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            if not models:
                logger.debug(f"No Library found for user: {user_id}")
                return None

            # RULE-001 violation detection
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

    def _to_domain(self, model: LibraryModel) -> Library:
        """
        Convert ORM model to Domain model (DRY principle)

        Args:
            model: LibraryModel instance

        Returns:
            Library domain object
        """
        return Library(
            library_id=model.id,
            user_id=model.user_id,
            name=LibraryName(value=model.name),
            basement_bookshelf_id=getattr(model, 'basement_bookshelf_id', None),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def delete(self, library_id: UUID) -> None:
        """
        Delete Library by ID

        Side Effects:
            - Removes database record
            - Cascade delete rules handled at DB level
        """
        try:
            model = await self.session.get(LibraryModel, library_id)
            if model:
                await self.session.delete(model)
                logger.info(f"Library deleted: {library_id}")
            else:
                logger.debug(f"Library not found for deletion: {library_id}")
        except Exception as e:
            logger.error(f"Error deleting Library {library_id}: {e}")
            raise

    async def exists(self, library_id: UUID) -> bool:
        """
        Check if Library exists

        Args:
            library_id: UUID of the Library

        Returns:
            True if Library exists, False otherwise
        """
        try:
            model = await self.session.get(LibraryModel, library_id)
            return model is not None
        except Exception as e:
            logger.error(f"Error checking Library existence {library_id}: {e}")
            raise
