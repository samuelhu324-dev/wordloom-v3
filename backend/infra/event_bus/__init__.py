"""
Event Bus Module - Domain Event Handling

Infrastructure for publishing and handling domain events.

Structure:
  - event_bus.py: Event bus adapter (interface + implementation)
  - handlers/: Event handlers (one handler per event type)

Domain events flow:
  1. Domain layer emits event (e.g., MediaUploaded)
  2. UseCase layer publishes to EventBus
  3. EventBus routes to registered handlers
  4. Handlers execute side effects (e.g., schedule 30-day purge)

No domain code depends on this module.
"""
