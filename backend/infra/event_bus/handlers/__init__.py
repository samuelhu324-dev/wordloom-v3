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

import logging

logger = logging.getLogger(__name__)

# Import handler modules to trigger @EventHandlerRegistry.register decorators.
# Important: import each module independently so a broken handler doesn't prevent
# other handlers (especially search_index_handlers) from being registered.

_handler_module_names = [
    "search_index_handlers",
    "bookshelf_handler",
    "media_handler",
    "chronicle_handler",
]

for _mod in _handler_module_names:
    try:
        __import__(f"{__name__}.{_mod}")
    except ImportError as e:
        logger.warning(f"Could not import handler module: {e}")

__all__ = list(_handler_module_names)


