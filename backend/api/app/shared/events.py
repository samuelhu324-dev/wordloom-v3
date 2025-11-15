"""
Event bus infrastructure - Asynchronous domain event publishing

Provides:
- EventBus: Core event publisher
- Event handler registration and dispatch

Pattern: Observer pattern with async support
"""

import asyncio
from typing import Callable, Dict, List, Type, Optional
from shared.base import DomainEvent
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Asynchronous event bus - publishes domain events to handlers

    Purpose:
    - Decouple domain from infrastructure via events
    - Enable side effects (notifications, audit logs, cascade operations)
    - Support event handlers registration and dispatch

    Pattern: Observer pattern with async support

    Usage:
        event_bus = EventBus()

        # Subscribe handler at startup
        event_bus.subscribe(BookCreatedEvent, on_book_created)

        # Publish event from domain
        book = Book.create(...)
        await event_bus.publish(book.get_events()[0])
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        Subscribe handler to event type

        Args:
            event_type: DomainEvent subclass to listen for
            handler: async callable(event) -> None

        Raises:
            TypeError: If handler is not callable
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all subscribers

        Args:
            event: DomainEvent instance to publish

        Note:
        - Handlers run concurrently (asyncio.gather)
        - Failures in one handler don't stop others
        - All exceptions are logged
        """
        event_type = type(event)

        if event_type not in self._handlers:
            logger.debug(f"No handlers registered for {event_type.__name__}")
            return

        handlers = self._handlers[event_type]
        logger.info(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")

        # Run all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handlers[i].__name__} failed: {result}",
                    exc_info=result,
                )

    def get_subscribers_count(self, event_type: Type[DomainEvent]) -> int:
        """
        Get number of subscribers for event type

        Args:
            event_type: DomainEvent subclass

        Returns:
            int: Number of registered handlers
        """
        return len(self._handlers.get(event_type, []))

    def get_all_subscriptions(self) -> Dict[Type[DomainEvent], List[str]]:
        """
        Get summary of all subscriptions

        Returns:
            Dict mapping event types to handler names
        """
        return {
            event_type: [h.__name__ for h in handlers]
            for event_type, handlers in self._handlers.items()
        }


# Global event bus singleton
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get or create global event bus singleton

    Returns:
        EventBus: Global event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        logger.info("Initialized global EventBus")
    return _event_bus

