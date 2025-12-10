"""
Domain Event Handlers - Side effect implementations for domain events

This module contains all event handler implementations that execute side effects
when domain events are published.

Architecture:
- Handlers are registered via @EventHandlerRegistry.register decorator
- Each handler is an async function
- Handlers are completely decoupled from domain logic
- Domain layer never imports from this module

Handler Organization:
- bookshelf_handler.py: BookshelfDeleted → cascade to books
- media_handler.py: MediaUploaded/Restored/Purged → background jobs

At Application Startup (main.py):
    from backend.infra.event_bus.event_handler_registry import EventHandlerRegistry

    # Import handler modules to trigger @register decorators
    from backend.infra.event_bus.handlers import bookshelf_handler, media_handler

    # Bootstrap all registered handlers to EventBus
    EventHandlerRegistry.bootstrap()

After bootstrap, all domain events will automatically route to their handlers.
"""

# Import all handler modules to trigger decorator registration
# (This should also be done in main.py for clarity)
try:
    from . import bookshelf_handler, media_handler, chronicle_handler
except ImportError as e:
    # If a handler module has unresolved imports, skip it
    # This can happen during development
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import handler module: {e}")

__all__ = ["bookshelf_handler", "media_handler", "chronicle_handler"]


