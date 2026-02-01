"""
Bookshelf Service - Business logic orchestration

Service layer responsibilities:
- Business rule validation (checking pre-conditions)
- Domain logic orchestration (calling Domain methods)
- Repository coordination (persistence)
- Domain Event publishing (notifying other modules)
- Error translation (Domain Exceptions to callers)
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from api.app.modules.bookshelf.domain import Bookshelf, BookshelfStatus
from api.app.modules.bookshelf.application.ports.output import BookshelfRepository
from api.app.modules.bookshelf.exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
)

logger = logging.getLogger(__name__)


class BookshelfService:
    """Service for managing Bookshelf aggregate

    Architecture:
    - Layer 1: Validation (business rules)
    - Layer 2: Domain Logic (calling Domain methods)
    - Layer 3: Persistence (Repository)
    - Layer 4: Event Publishing (async listeners)
    """

    def __init__(self, repository: BookshelfRepository, event_bus=None):
        """
        Initialize service with repository and optional event bus

        Args:
            repository: BookshelfRepository instance for persistence
            event_bus: Optional event bus for publishing DomainEvents
        """
        self.repository = repository
        self.event_bus = event_bus

    async def create_bookshelf(
        self,
        library_id: UUID,
        name: str,
        description: str = None,
    ) -> Bookshelf:
        """
        Create a new Bookshelf

        Business logic:
        - Validate library_id exists (FK constraint)
        - Check for duplicate name within Library (RULE-006)
        - Create Bookshelf aggregate
        - Persist and publish events

        Args:
            library_id: UUID of parent Library
            name: Name for the Bookshelf
            description: Optional description

        Returns:
            Created Bookshelf aggregate

        Raises:
            ValueError: If name is invalid
            BookshelfAlreadyExistsError: If name already exists in Library
        """
        logger.info(f"Creating Bookshelf in Library {library_id} with name '{name}'")

        # ========== Layer 1: Validation ==========
        # Check for duplicate name within Library (RULE-006)
        if await self.repository.exists_by_name(library_id, name):
            logger.warning(f"Bookshelf name already exists in Library {library_id}: {name}")
            raise BookshelfAlreadyExistsError(
                f"Bookshelf with name '{name}' already exists in this Library"
            )

        # ========== Layer 2: Domain Logic ==========
        bookshelf = Bookshelf.create(
            library_id=library_id,
            name=name,
            description=description,
        )
        logger.debug(f"Created Bookshelf domain object: {bookshelf.id}")

        # ========== Layer 3: Persistence ==========
        try:
            await self.repository.save(bookshelf)
            logger.info(f"Bookshelf persisted: {bookshelf.id}")
        except IntegrityError as e:
            logger.error(f"IntegrityError while saving Bookshelf: {e}")
            raise BookshelfAlreadyExistsError("Bookshelf already exists")

        # ========== Layer 4: Event Publishing ==========
        if self.event_bus and bookshelf.events:
            logger.debug(f"Publishing {len(bookshelf.events)} domain events")
            for event in bookshelf.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish event {event.__class__.__name__}: {e}")

        return bookshelf

    async def get_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """
        Retrieve Bookshelf by ID

        Args:
            bookshelf_id: UUID of the Bookshelf

        Returns:
            Bookshelf aggregate

        Raises:
            BookshelfNotFoundError: If Bookshelf not found
        """
        logger.debug(f"Retrieving Bookshelf: {bookshelf_id}")
        bookshelf = await self.repository.get_by_id(bookshelf_id)
        if not bookshelf:
            logger.warning(f"Bookshelf not found: {bookshelf_id}")
            raise BookshelfNotFoundError(f"Bookshelf {bookshelf_id} not found")
        logger.debug(f"Bookshelf retrieved: {bookshelf_id}")
        return bookshelf

    async def list_bookshelves(self, library_id: UUID) -> List[Bookshelf]:
        """
        List all Bookshelves in a Library (excluding deleted)

        Supports RULE-005: Bookshelf 必须属于一个 Library

        Args:
            library_id: UUID of the Library

        Returns:
            List of active Bookshelves
        """
        logger.debug(f"Listing Bookshelves for Library: {library_id}")
        return await self.repository.get_by_library_id(library_id)

    async def get_basement_bookshelf(self, library_id: UUID) -> Bookshelf:
        """
        Get the Basement Bookshelf for a Library

        Supports RULE-010: 每个 Library 自动创建一个 Basement Bookshelf

        Args:
            library_id: UUID of the Library

        Returns:
            Basement Bookshelf aggregate

        Raises:
            BookshelfNotFoundError: If Basement not found
        """
        logger.debug(f"Retrieving Basement for Library: {library_id}")
        basement = await self.repository.get_basement_by_library_id(library_id)
        if not basement:
            logger.error(f"Basement not found for Library: {library_id}")
            raise BookshelfNotFoundError(f"Basement Bookshelf not found for Library {library_id}")
        return basement

    async def rename_bookshelf(self, bookshelf_id: UUID, new_name: str) -> Bookshelf:
        """
        Rename a Bookshelf

        Args:
            bookshelf_id: UUID of the Bookshelf
            new_name: New name for the Bookshelf

        Returns:
            Updated Bookshelf aggregate

        Raises:
            BookshelfNotFoundError: If Bookshelf not found
            ValueError: If new_name is invalid
        """
        logger.info(f"Renaming Bookshelf {bookshelf_id} to '{new_name}'")
        bookshelf = await self.get_bookshelf(bookshelf_id)

        # Rename (emits BookshelfRenamed event)
        bookshelf.rename(new_name)

        # Persist changes
        await self.repository.save(bookshelf)

        # Publish event
        if self.event_bus and bookshelf.events:
            for event in bookshelf.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish rename event: {e}")

        return bookshelf

    # ========================================================================
    # Auxiliary Features (Service-layer metadata operations per AD-004)
    # ========================================================================

    async def _toggle_property(
        self,
        bookshelf_id: UUID,
        property_name: str,
        value: bool,
        timestamp_property: str = None,
    ) -> Bookshelf:
        """
        Generic helper for toggling boolean properties (DRY principle)

        Args:
            bookshelf_id: UUID of the Bookshelf
            property_name: Name of the boolean property to toggle
            value: Boolean value to set
            timestamp_property: Optional timestamp property to update (e.g., 'pinned_at')

        Returns:
            Updated Bookshelf aggregate
        """
        bookshelf = await self.get_bookshelf(bookshelf_id)
        current = getattr(bookshelf, property_name, None)

        if current != value:
            setattr(bookshelf, property_name, value)
            if timestamp_property and value:
                setattr(bookshelf, timestamp_property, datetime.utcnow())
            elif timestamp_property and not value:
                setattr(bookshelf, timestamp_property, None)
            bookshelf.updated_at = datetime.utcnow()
            await self.repository.save(bookshelf)
            logger.debug(f"Toggled {property_name} to {value} for Bookshelf {bookshelf_id}")

        return bookshelf

    async def set_description(self, bookshelf_id: UUID, description: str = None) -> Bookshelf:
        """Set or update Bookshelf description (Service-layer metadata operation)"""
        logger.info(f"Setting description for Bookshelf {bookshelf_id}")
        from api.app.modules.bookshelf.domain import BookshelfDescription
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.description = BookshelfDescription(value=description)
        bookshelf.updated_at = datetime.utcnow()
        await self.repository.save(bookshelf)
        return bookshelf

    async def pin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Pin a Bookshelf to top (Service-layer auxiliary feature)"""
        return await self._toggle_property(bookshelf_id, "is_pinned", True, "pinned_at")

    async def unpin_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unpin a Bookshelf (Service-layer auxiliary feature)"""
        return await self._toggle_property(bookshelf_id, "is_pinned", False, "pinned_at")

    async def favorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Mark Bookshelf as favorite (Service-layer auxiliary feature)"""
        return await self._toggle_property(bookshelf_id, "is_favorite", True)

    async def unfavorite_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unmark Bookshelf as favorite (Service-layer auxiliary feature)"""
        return await self._toggle_property(bookshelf_id, "is_favorite", False)

    async def archive_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Archive a Bookshelf (Service-layer auxiliary feature)"""
        logger.info(f"Archiving Bookshelf {bookshelf_id}")
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.change_status(BookshelfStatus.ARCHIVED)
        await self.repository.save(bookshelf)
        return bookshelf

    async def unarchive_bookshelf(self, bookshelf_id: UUID) -> Bookshelf:
        """Unarchive a Bookshelf (Service-layer auxiliary feature)"""
        logger.info(f"Unarchiving Bookshelf {bookshelf_id}")
        bookshelf = await self.get_bookshelf(bookshelf_id)
        bookshelf.change_status(BookshelfStatus.ACTIVE)
        await self.repository.save(bookshelf)
        return bookshelf

    async def delete_bookshelf(self, bookshelf_id: UUID) -> None:
        """
        Delete a Bookshelf (soft delete via Basement pattern)

        Implements POLICY-003: Bookshelf 删除时的 Book 处理
        - 查询所有 Books
        - 对每个 Book 转移到 Basement（软删除）
        - 标记 Bookshelf 为已删除
        - 发布 BookshelfDeleted 事件

        Note: Book 级联转移由 book_service 处理
        Note: Block 级联由 Book delete 时处理

        Args:
            bookshelf_id: UUID of the Bookshelf to delete

        Raises:
            BookshelfNotFoundError: If Bookshelf not found
        """
        logger.info(f"Deleting Bookshelf: {bookshelf_id}")
        bookshelf = await self.get_bookshelf(bookshelf_id)

        # Mark deleted (emits BookshelfDeleted event)
        # Note: 实际的 Books 级联转移应由 DomainService 或 EventListener 处理
        # 这里只进行 soft delete 标记
        bookshelf.mark_deleted()

        # Persist deletion (soft delete only)
        await self.repository.save(bookshelf)
        logger.info(f"Bookshelf marked as deleted: {bookshelf_id}")

        # Publish event
        if self.event_bus and bookshelf.events:
            for event in bookshelf.events:
                try:
                    await self.event_bus.publish(event)
                    logger.debug(f"Published event: {event.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Failed to publish delete event: {e}")

        # Note: 不进行物理删除，Basement 模式的转移由事件监听处理

    # ========================================================================
    # Query Methods (Moved from Domain)
    # ========================================================================

    async def can_accept_books(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf can accept new Books (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status != BookshelfStatus.DELETED

    async def is_active(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is active (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.ACTIVE

    async def is_archived(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is archived (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.ARCHIVED

    async def is_deleted(self, bookshelf_id: UUID) -> bool:
        """Check if Bookshelf is deleted (Service-layer query)"""
        bookshelf = await self.get_bookshelf(bookshelf_id)
        return bookshelf.status == BookshelfStatus.DELETED
