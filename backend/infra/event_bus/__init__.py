"""
Event Bus Module - Domain Event Handling Infrastructure

Provides the core infrastructure for asynchronous domain event publishing and handling.

Components:
  - event_handler_registry.py: Central registry for event handlers
  - handlers/: Event handler implementations (one file per domain)

Architecture:
  1. Domain layer emits events when business logic completes
  2. UseCase layer adds events to aggregate root
  3. Repository layer persists aggregate and publishes events to EventBus
  4. EventBus routes events to registered handlers (async)
  5. Handlers execute side effects (cascades, notifications, scheduled jobs, etc.)

Event Flow:
    Domain Layer (emit event)
         ↓
    UseCase Layer (aggregate.add_event())
         ↓
    Application Layer (repository.save(aggregate))
         ↓
    EventBus.publish(event)
         ↓
    Registered Handlers (side effects)

No domain code depends on this module.
This is purely infrastructure.

Usage at application startup (main.py):
    from backend.infra.event_bus.event_handler_registry import EventHandlerRegistry

    # Bootstrap all handlers to EventBus
    EventHandlerRegistry.bootstrap()
"""

from .event_handler_registry import EventHandlerRegistry

__all__ = ["EventHandlerRegistry"]

