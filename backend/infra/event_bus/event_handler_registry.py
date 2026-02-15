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
import inspect
import importlib
import os

if TYPE_CHECKING:
    from api.app.shared.base import DomainEvent

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
    def _wants_session(cls, handler: Callable) -> bool:
        try:
            params = list(inspect.signature(handler).parameters.values())
        except (TypeError, ValueError):
            return False
        return len(params) >= 2

    @classmethod
    def _get_tx_mode(cls) -> str:
        """Transaction mode for a single event dispatch.

        Values:
        - savepoint: single outer transaction; each DB handler runs in begin_nested();
                    failures roll back to the savepoint and do NOT stop other handlers.
        - atomic:    single outer transaction; any handler failure aborts remaining handlers
                    and rolls back the whole event.
        - none:      do not create a DB session/transaction here.

        Default: savepoint (closest to legacy EventBus behavior: other handlers still run).
        """

        return os.getenv("WORDLOOM_EVENT_BUS_TX_MODE", "savepoint").strip().lower()

    @classmethod
    def _make_dispatcher(cls, event_type: Type["DomainEvent"]) -> Callable:
        """Create the single EventBus subscriber for an event type.

        The dispatcher is responsible for opening an AsyncSession and managing
        transaction boundaries for all handlers of this event.
        """

        handlers = list(cls._handlers.get(event_type, []))
        handlers_with_session = [h for h in handlers if cls._wants_session(h)]

        async def _dispatcher(event):
            tx_mode = cls._get_tx_mode()

            # If no handler wants DB access (or tx mode disabled), don't create a session.
            if not handlers_with_session or tx_mode == "none":
                for handler in handlers:
                    await handler(event)
                return

            from infra.database.session import get_session_factory

            session_factory = await get_session_factory()
            async with session_factory() as session:
                if tx_mode == "atomic":
                    try:
                        async with session.begin():
                            for handler in handlers:
                                if cls._wants_session(handler):
                                    await handler(event, session)
                                else:
                                    await handler(event)

                        logger.info(
                            {
                                "event": "event_bus.uow",
                                "event_type": event_type.__name__,
                                "mode": "atomic",
                                "outcome": "committed",
                            }
                        )
                    except Exception:
                        await session.rollback()
                        logger.info(
                            {
                                "event": "event_bus.uow",
                                "event_type": event_type.__name__,
                                "mode": "atomic",
                                "outcome": "rolled_back",
                            }
                        )
                        raise

                    return

                # Default: savepoint mode
                errors: List[tuple[str, Exception]] = []
                async with session.begin():
                    for handler in handlers:
                        handler_name = getattr(handler, "__name__", str(handler))
                        if cls._wants_session(handler):
                            try:
                                async with session.begin_nested():
                                    await handler(event, session)
                            except Exception as exc:
                                errors.append((handler_name, exc))
                                logger.error(
                                    "Event handler failed (savepoint rolled back): %s → %s",
                                    handler_name,
                                    event_type.__name__,
                                    exc_info=True,
                                )
                                continue
                        else:
                            try:
                                await handler(event)
                            except Exception as exc:
                                errors.append((handler_name, exc))
                                logger.error(
                                    "Event handler failed (no DB savepoint available): %s → %s",
                                    handler_name,
                                    event_type.__name__,
                                    exc_info=True,
                                )
                                continue

                logger.info(
                    {
                        "event": "event_bus.uow",
                        "event_type": event_type.__name__,
                        "mode": "savepoint",
                        "outcome": "committed_with_errors" if errors else "committed",
                        "error_count": len(errors),
                    }
                )

        _dispatcher.__name__ = f"dispatch_{event_type.__name__}"
        return _dispatcher

    @classmethod
    def _wrap_for_event_bus(cls, handler: Callable) -> Callable:
        """Wrap handler with UoW when it declares a DB/session parameter.

        Supported handler signatures:
        - async def handler(event) -> None
        - async def handler(event, db_session) -> None

        For the 2-arg form, we open an AsyncSession and manage commit/rollback here.
        This keeps transaction boundaries out of individual handlers.
        """

        try:
            params = list(inspect.signature(handler).parameters.values())
        except (TypeError, ValueError):
            params = []

        wants_session = len(params) >= 2

        if not wants_session:
            return handler

        async def _wrapped(event):
            # Lazy import to avoid startup import cycles
            from infra.database.session import get_session_factory

            session_factory = await get_session_factory()
            async with session_factory() as session:
                try:
                    await handler(event, session)
                    await session.commit()
                    logger.info(
                        {
                            "event": "event_bus.uow",
                            "handler": getattr(handler, "__name__", str(handler)),
                            "outcome": "committed",
                        }
                    )
                except Exception:
                    await session.rollback()
                    logger.info(
                        {
                            "event": "event_bus.uow",
                            "handler": getattr(handler, "__name__", str(handler)),
                            "outcome": "rolled_back",
                        }
                    )
                    raise

        _wrapped.__name__ = getattr(handler, "__name__", "wrapped_handler")
        return _wrapped

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
        get_event_bus = None
        for module_name in ("api.app.shared.events", "app.shared.events"):
            try:
                module = importlib.import_module(module_name)
                get_event_bus = getattr(module, "get_event_bus")
                break
            except Exception:
                continue

        if get_event_bus is None:
            raise ImportError("Could not import get_event_bus from api.app.shared.events or app.shared.events")

        event_bus = get_event_bus()

        handler_count = 0
        for event_type, handlers in cls._handlers.items():
            # Subscribe a single dispatcher per event type.
            # This enables single-event single-transaction semantics.
            event_bus.subscribe(event_type, cls._make_dispatcher(event_type))
            handler_count += len(handlers)

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

