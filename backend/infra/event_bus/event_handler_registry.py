"""
Event Handler Registry - Central registration point for event handlers

Purpose:
- Register all event handlers at application startup
- Avoid circular imports between modules
- Provide discoverability and management of handlers
- Enable hot-reload in development environment

Pattern: Registry pattern + Decorator-based registration

Usage at startup:
    from backend.infra.event_bus.event_handler_registry import EventHandlerRegistry

    # Register all handlers
    EventHandlerRegistry.bootstrap()

    # Handlers are now subscribed to EventBus
"""

from typing import Dict, Type, Callable, List, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.shared.base import DomainEvent

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """
    Central registry for event handlers

    Responsibilities:
    1. Register event handlers via @register decorator
    2. Collect all handlers from all modules
    3. Bootstrap handlers to EventBus at startup
    4. Provide introspection (list all registered handlers)

    Example:
        # In any handler file (e.g., backend/infra/event_bus/handlers/media_handler.py)
        @EventHandlerRegistry.register(MediaUploaded)
        async def on_media_uploaded(event: MediaUploaded):
            logger.info(f"Media uploaded: {event.media_id}")
            # Schedule 30-day purge
            await schedule_purge_job(event.media_id, delay_days=30)

        # At application startup (main.py)
        EventHandlerRegistry.bootstrap()
    """

    _handlers: Dict[Type["DomainEvent"], List[Callable]] = {}

    @classmethod
    def register(cls, event_type: Type["DomainEvent"]):
        """
        Decorator to register event handler

        Args:
            event_type: DomainEvent subclass to handle

        Returns:
            Decorator function
        """
        def decorator(handler: Callable):
            if event_type not in cls._handlers:
                cls._handlers[event_type] = []

            cls._handlers[event_type].append(handler)
            logger.debug(f"Registered handler: {handler.__name__} → {event_type.__name__}")
            return handler

        return decorator

    @classmethod
    def bootstrap(cls) -> None:
        """
        Bootstrap all registered handlers to the global EventBus

        Called at application startup (in main.py)
        After this call, EventBus will route events to all registered handlers

        Side effects:
        - Subscribes all handlers to EventBus
        - Logs registration summary
        """
        # Import here to avoid circular dependency
        from app.shared.events import get_event_bus

        event_bus = get_event_bus()

        handler_count = 0
        for event_type, handlers in cls._handlers.items():
            for handler in handlers:
                event_bus.subscribe(event_type, handler)
                handler_count += 1

        logger.info(
            f"EventHandlerRegistry bootstrapped: "
            f"{len(cls._handlers)} event types, {handler_count} total handlers"
        )

    @classmethod
    def get_all(cls) -> Dict[Type["DomainEvent"], List[Callable]]:
        """
        Get all registered handlers (read-only copy)

        Returns:
            Dict mapping event types to handler lists
        """
        return {
            event_type: list(handlers)
            for event_type, handlers in cls._handlers.items()
        }

    @classmethod
    def get_handlers_for_event(cls, event_type: Type["DomainEvent"]) -> List[Callable]:
        """
        Get handlers for specific event type

        Args:
            event_type: DomainEvent subclass

        Returns:
            List of handler functions
        """
        return cls._handlers.get(event_type, [])

    @classmethod
    def get_registration_summary(cls) -> Dict[str, Any]:
        """
        Get summary of all registrations (for debugging/monitoring)

        Returns:
            Dict with registration statistics
        """
        total_events = len(cls._handlers)
        total_handlers = sum(len(h) for h in cls._handlers.values())

        summary = {
            "total_event_types": total_events,
            "total_handlers": total_handlers,
            "events": {
                event_type.__name__: len(handlers)
                for event_type, handlers in cls._handlers.items()
            },
        }

        return summary

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registrations (for testing only)

        WARNING: This should only be used in test teardown
        """
        cls._handlers.clear()
        logger.warning("EventHandlerRegistry cleared (should only happen in tests)")

