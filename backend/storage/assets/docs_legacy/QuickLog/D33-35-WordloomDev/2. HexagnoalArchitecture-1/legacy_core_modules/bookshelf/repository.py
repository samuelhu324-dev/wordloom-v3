"""
Bookshelf Repository - Data access abstraction

Responsibilities:
- Translating between Domain model and ORM model
- Executing database queries
- Handling database constraints and errors
- No business logic here - that's the Domain's job
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from modules.bookshelf.domain import Bookshelf
from modules.bookshelf.models import BookshelfModel
from modules.bookshelf.exceptions import BookshelfAlreadyExistsError

logger = logging.getLogger(__name__)


class BookshelfRepository(ABC):
    """Abstract Repository interface for Bookshelf aggregate"""

    @abstractmethod
    async def save(self, bookshelf: Bookshelf) -> None:
        """Save Bookshelf aggregate to database"""
        pass

    @abstractmethod
    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        """Retrieve Bookshelf by ID"""
        pass

    @abstractmethod
    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        """Retrieve all active Bookshelves in a Library (RULE-005)"""
        pass

    @abstractmethod
    async def get_basement_by_library_id(self, library_id: UUID) -> Optional[Bookshelf]:
        """Retrieve Basement Bookshelf for a Library (RULE-010)"""
        pass

    @abstractmethod
    async def exists_by_name(self, library_id: UUID, name: str) -> bool:
        """Check if Bookshelf with name exists in Library (RULE-006)"""
        pass

    @abstractmethod
    async def delete(self, bookshelf_id: UUID) -> None:
        """Delete Bookshelf by ID (Note: should be soft delete only)"""
        pass

    @abstractmethod
    async def exists(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf exists"""
        pass


class BookshelfRepositoryImpl(BookshelfRepository):
    """Concrete implementation of BookshelfRepository using SQLAlchemy"""

    def __init__(self, session):
        """Initialize repository with database session"""
        self.session = session

    async def save(self, bookshelf: Bookshelf) -> None:
        """
        Save Bookshelf aggregate to database

        Handles constraint violations by converting to Domain exceptions.

        Raises:
            BookshelfAlreadyExistsError: If unique constraint violated
        """
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
        except IntegrityError as e:
            # Transform database constraint violation into Domain exception
            error_str = str(e).lower()
            if "library_id" in error_str or "name" in error_str:
                logger.warning(f"Integrity constraint violated: {e}")
                raise BookshelfAlreadyExistsError(
                    "Bookshelf with this name already exists in Library"
                )
            logger.error(f"Unexpected integrity error: {e}")
            raise

    async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
        """
        Retrieve Bookshelf by ID

        Raises:
            Exception: If database query fails
        """
        try:
            model = await self.session.get(BookshelfModel, bookshelf_id)
            if not model:
                logger.debug(f"Bookshelf not found: {bookshelf_id}")
                return None
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Bookshelf {bookshelf_id}: {e}")
            raise

    async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
        """
        Retrieve all active Bookshelves in a Library

        Supports RULE-005: Bookshelf 必须属于一个 Library

        Raises:
            Exception: If database query fails
        """
        try:
            stmt = select(BookshelfModel).where(
                (BookshelfModel.library_id == library_id)
                & (BookshelfModel.status != "DELETED")  # Exclude deleted
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            logger.debug(f"Retrieved {len(models)} Bookshelves for Library {library_id}")
            return [self._to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Error fetching Bookshelves for Library {library_id}: {e}")
            raise

    async def get_basement_by_library_id(self, library_id: UUID) -> Optional[Bookshelf]:
        """
        Retrieve Basement Bookshelf for a Library

        Supports RULE-010: 每个 Library 自动创建一个 Basement Bookshelf

        Raises:
            Exception: If database query fails
        """
        try:
            stmt = select(BookshelfModel).where(
                (BookshelfModel.library_id == library_id)
                & (BookshelfModel.name == "Basement")  # Basement 特殊标记
            )
            result = await self.session.execute(stmt)
            model = result.scalars().first()
            if not model:
                logger.debug(f"Basement not found for Library {library_id}")
                return None
            logger.debug(f"Retrieved Basement for Library {library_id}")
            return self._to_domain(model)
        except Exception as e:
            logger.error(f"Error fetching Basement for Library {library_id}: {e}")
            raise

    async def exists_by_name(self, library_id: UUID, name: str) -> bool:
        """
        Check if Bookshelf with name exists in Library

        Supports RULE-006: Bookshelf 的名称不能为空（同名检查）

        Args:
            library_id: UUID of the Library
            name: Name to check

        Returns:
            True if name exists in Library, False otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            stmt = select(BookshelfModel).where(
                (BookshelfModel.library_id == library_id)
                & (BookshelfModel.name == name)
                & (BookshelfModel.status != "DELETED")  # Exclude deleted
            )
            result = await self.session.execute(stmt)
            exists = result.scalars().first() is not None
            logger.debug(f"Bookshelf name '{name}' exists in Library {library_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking Bookshelf name for Library {library_id}: {e}")
            raise

    async def delete(self, bookshelf_id: UUID) -> None:
        """
        Delete Bookshelf by ID

        Note: In Basement pattern, we should NOT hard delete.
        This method exists for compatibility but should rarely be called.

        Side Effects:
            - Cascade delete rules handled at DB level (if configured)
        """
        try:
            model = await self.session.get(BookshelfModel, bookshelf_id)
            if model:
                await self.session.delete(model)
                logger.info(f"Bookshelf deleted: {bookshelf_id}")
            else:
                logger.debug(f"Bookshelf not found for deletion: {bookshelf_id}")
        except Exception as e:
            logger.error(f"Error deleting Bookshelf {bookshelf_id}: {e}")
            raise

    async def exists(self, bookshelf_id: UUID) -> bool:
        """
        Check if Bookshelf exists

        Args:
            bookshelf_id: UUID of the Bookshelf

        Returns:
            True if Bookshelf exists, False otherwise
        """
        try:
            model = await self.session.get(BookshelfModel, bookshelf_id)
            return model is not None
        except Exception as e:
            logger.error(f"Error checking Bookshelf existence {bookshelf_id}: {e}")
            raise

    def _to_domain(self, model: BookshelfModel) -> Bookshelf:
        """
        Convert ORM model to Domain model (DRY principle)

        Args:
            model: BookshelfModel instance

        Returns:
            Bookshelf domain object
        """
        from modules.bookshelf.domain import (
            BookshelfName,
            BookshelfDescription,
            BookshelfStatus,
        )
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
