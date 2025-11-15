"""
Bookshelf Cascade Event Handlers

Handles domain events from Bookshelf module:
- BookshelfDeleted: Cascade to related books and blocks
- BookshelfArchived: Update book status
- BookshelfNameChanged: Update audit log

Pattern: Event handlers registered via @EventHandlerRegistry.register decorator
All handlers are async functions that implement side effects.
"""

import logging
from typing import TYPE_CHECKING
from app.shared.base import DomainEvent
from backend.infra.event_bus.event_handler_registry import EventHandlerRegistry

logger = logging.getLogger(__name__)


@EventHandlerRegistry.register(DomainEvent)  # Placeholder - actual event type injected at runtime
async def on_bookshelf_deleted(event: DomainEvent) -> None:
    """
    Handle BookshelfDeleted event

    Side effect: Cascade deletion to books in this bookshelf
    - Move books to Basement (or delete, per RULE-010)
    - Cascade delete related blocks

    Args:
        event: BookshelfDeleted domain event

    TODO:
    - Implement cascade to Books application layer
    - Handle block deletion via Book aggregate
    - Log audit trail
    """
    logger.info(f"[Event] BookshelfDeleted: {getattr(event, 'bookshelf_id', 'unknown')}")
    logger.info(f"  Library: {getattr(event, 'library_id', 'unknown')}")
    logger.info(f"  Books affected: {getattr(event, 'books_count', 'unknown')}")
    # TODO: Call BookService.cascade_delete_bookshelf(event.bookshelf_id, event.library_id)


@EventHandlerRegistry.register(DomainEvent)
async def on_bookshelf_archived(event: DomainEvent) -> None:
    """
    Handle BookshelfArchived event

    Side effect: Update books to archived status or freeze them

    Args:
        event: BookshelfArchived domain event

    TODO:
    - Update all books in bookshelf to archived status
    - Freeze book modifications
    """
    logger.info(f"[Event] BookshelfArchived: {getattr(event, 'bookshelf_id', 'unknown')}")
    # TODO: Call BookService.archive_bookshelf_books(event.bookshelf_id)
