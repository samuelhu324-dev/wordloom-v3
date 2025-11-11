"""
Library Service - Business logic orchestration

Service layer handles:
- Coordinating between Repository and Domain
- Emitting Domain Events
- Application-level transactions
- Business rule enforcement
"""

from typing import Optional
from uuid import UUID

from domains.library.domain import Library
from domains.library.repository import LibraryRepository
from domains.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
)


class LibraryService:
    """
    Service for managing Library aggregate

    Business operations:
    - Create Library for user
    - Rename Library
    - Retrieve Library
    - Delete Library
    """

    def __init__(self, repository: LibraryRepository):
        """
        Initialize service with repository

        Args:
            repository: LibraryRepository instance for persistence
        """
        self.repository = repository

    async def create_library(self, user_id: UUID, name: str) -> Library:
        """
        Create a new Library for user

        Business logic:
        - Check if user already has a Library (one per user rule)
        - Create Library aggregate
        - Save to repository
        - Emit LibraryCreated event

        Args:
            user_id: UUID of the user
            name: Name for the Library

        Returns:
            Created Library aggregate

        Raises:
            LibraryAlreadyExistsError: If user already has a Library
            ValueError: If name is invalid
        """
        # Check if Library already exists for this user
        existing = await self.repository.get_by_user_id(user_id)
        if existing:
            raise LibraryAlreadyExistsError(
                f"User {user_id} already has a Library"
            )

        # Create Library aggregate (emits LibraryCreated event)
        library = Library.create(user_id=user_id, name=name)

        # Persist to database
        await self.repository.save(library)

        return library

    async def get_library(self, library_id: UUID) -> Library:
        """
        Retrieve Library by ID

        Args:
            library_id: UUID of the Library

        Returns:
            Library aggregate

        Raises:
            LibraryNotFoundError: If Library not found
        """
        library = await self.repository.get_by_id(library_id)
        if not library:
            raise LibraryNotFoundError(f"Library {library_id} not found")
        return library

    async def get_user_library(self, user_id: UUID) -> Library:
        """
        Retrieve Library for a user (one Library per user)

        Args:
            user_id: UUID of the user

        Returns:
            Library aggregate

        Raises:
            LibraryNotFoundError: If user has no Library
        """
        library = await self.repository.get_by_user_id(user_id)
        if not library:
            raise LibraryNotFoundError(
                f"No Library found for user {user_id}"
            )
        return library

    async def rename_library(self, library_id: UUID, new_name: str) -> Library:
        """
        Rename a Library

        Args:
            library_id: UUID of the Library
            new_name: New name for the Library

        Returns:
            Updated Library aggregate

        Raises:
            LibraryNotFoundError: If Library not found
            ValueError: If new_name is invalid
        """
        library = await self.get_library(library_id)

        # Rename (emits LibraryRenamed event)
        library.rename(new_name)

        # Persist changes
        await self.repository.save(library)

        return library

    async def delete_library(self, library_id: UUID) -> None:
        """
        Delete a Library

        This emits LibraryDeleted event. Cascade deletion of Bookshelves,
        Books, Blocks is handled at:
        - Domain Services layer (coordination)
        - Infrastructure layer (database cascade rules)

        Args:
            library_id: UUID of the Library to delete

        Raises:
            LibraryNotFoundError: If Library not found
        """
        library = await self.get_library(library_id)

        # Mark deleted (emits LibraryDeleted event)
        library.mark_deleted()

        # Persist deletion
        await self.repository.save(library)
        await self.repository.delete(library_id)
