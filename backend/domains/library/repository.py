"""
Library Repository - Data access abstraction

Defines the interface and implementation for persisting Library aggregates.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domains.library.domain import Library
from domains.library.models import LibraryModel


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
        """
        model = LibraryModel(
            id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            created_at=library.created_at,
            updated_at=library.updated_at,
        )
        self.session.add(model)
        # Note: Session commit is handled at application level (Unit of Work pattern)

    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """
        Retrieve Library by ID

        Translates from ORM model to Domain model.
        """
        model = await self.session.get(LibraryModel, library_id)
        if not model:
            return None

        from domains.library.domain import LibraryName
        return Library(
            library_id=model.id,
            user_id=model.user_id,
            name=LibraryName(value=model.name),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """
        Retrieve Library by user ID
        """
        from sqlalchemy import select
        stmt = select(LibraryModel).where(LibraryModel.user_id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalars().first()

        if not model:
            return None

        from domains.library.domain import LibraryName
        return Library(
            library_id=model.id,
            user_id=model.user_id,
            name=LibraryName(value=model.name),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def delete(self, library_id: UUID) -> None:
        """
        Delete Library by ID
        """
        model = await self.session.get(LibraryModel, library_id)
        if model:
            await self.session.delete(model)

    async def exists(self, library_id: UUID) -> bool:
        """
        Check if Library exists
        """
        model = await self.session.get(LibraryModel, library_id)
        return model is not None
