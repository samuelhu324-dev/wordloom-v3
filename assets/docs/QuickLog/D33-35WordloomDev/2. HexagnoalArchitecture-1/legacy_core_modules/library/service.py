"""
Library Service - Business logic orchestration

Service layer responsibilities:
- Business rule validation (checking pre-conditions)
- Domain logic orchestration (calling Domain methods)
- Repository coordination (persistence)
- Domain Event publishing (notifying other modules)
- Error translation (Domain Exceptions to callers)
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from modules.library.domain import Library
from modules.library.repository import LibraryRepository
from modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
)

logger = logging.getLogger(__name__)


class LibraryService:
    """
    Service for managing Library aggregate

    Business operations:
    - Create Library for user
    - Rename Library
    - Retrieve Library
    - Delete Library

    Architecture:
    - Layer 1: Validation (business rules)
    - Layer 2: Domain Logic (calling Domain methods)
    - Layer 3: Persistence (Repository)
    - Layer 4: Event Publishing (async listeners)
    """

    def __init__(self, repository: LibraryRepository, event_bus=None):
        """
        Initialize service with repository and optional event bus

        Args:
            repository: LibraryRepository instance for persistence
            event_bus: Optional event bus for publishing DomainEvents
        """
        self.repository = repository
        self.event_bus = event_bus

    async def create_library(self, user_id: UUID, name: str) -> Library:
        """
        Create a new Library for user

        Business logic:
        - Check if user already has a Library (one per user rule: RULE-001)
        - Create Library aggregate (emits LibraryCreated + BasementCreated events)
        - Save to repository
        - Publish events to event bus

        Args:
            user_id: UUID of the user
            name: Name for the Library

        Returns:
            Created Library aggregate

        Raises:
            LibraryAlreadyExistsError: If user already has a Library
            ValueError: If name is invalid
        """
        logger.info(f"Creating Library for user {user_id} with name '{name}'")

        # ========== Layer 1: Validation ==========
        # Check if Library already exists for this user (RULE-001)
        existing = await self.repository.get_by_user_id(user_id)
        if existing:
            logger.warning(f"User {user_id} already has a Library {existing.id}")
            raise LibraryAlreadyExistsError(
                f"User {user_id} already has a Library"
            )

        # ========== Layer 2: Domain Logic ==========
        # Create Library aggregate (emits LibraryCreated + BasementCreated events)
        library = Library.create(user_id=user_id, name=name)
        logger.debug(f"Created Library domain object: {library.id}")

        # ========== Layer 3: Persistence ==========
        # Persist to database
        try:
            await self.repository.save(library)
            logger.info(f"Library persisted: {library.id}")
        except IntegrityError as e:
            # Repository should handle IntegrityError, but catch it here as fallback
            logger.error(f"IntegrityError while saving Library: {e}")
            raise LibraryAlreadyExistsError("User already has a Library (database constraint)")
        except LibraryAlreadyExistsError:
            logger.warning(f"LibraryAlreadyExistsError from repository for user {user_id}")
            raise

        # ========== Layer 4: Event Publishing ==========
        # Publish collected domain events to event bus
        if self.event_bus and library.events:
            logger.debug(f"Publishing {len(library.events)} domain events")
            for event in library.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish event {event.__class__.__name__}: {e}")
                    # Note: We don't re-raise here because the Library was already persisted
                    # In production, you might use a dead-letter queue for failed events

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
        logger.debug(f"Retrieving Library: {library_id}")
        library = await self.repository.get_by_id(library_id)
        if not library:
            logger.warning(f"Library not found: {library_id}")
            raise LibraryNotFoundError(f"Library {library_id} not found")
        logger.debug(f"Library retrieved: {library_id}")
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
        logger.info(f"Renaming Library {library_id} to '{new_name}'")
        library = await self.get_library(library_id)

        # Rename (emits LibraryRenamed event)
        library.rename(new_name)

        # Persist changes
        await self.repository.save(library)

        # Publish event
        if self.event_bus and library.events:
            for event in library.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish rename event: {e}")

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
        logger.info(f"Deleting Library: {library_id}")
        library = await self.get_library(library_id)

        # Mark deleted (emits LibraryDeleted event)
        library.mark_deleted()

        # Persist deletion
        await self.repository.save(library)
        await self.repository.delete(library_id)
        logger.info(f"Library deleted successfully: {library_id}")

        # Publish event
        if self.event_bus and library.events:
            for event in library.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish delete event: {e}")
