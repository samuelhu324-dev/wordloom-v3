"""
Library Domain Layer - Public Interface

Purpose:
- Provide clean public interface for Library domain
- Hide internal implementation details
- Enable proper dependency inversion (consumers import from domain, not internals)

Structure:
- library.py: Library AggregateRoot
- library_name.py: LibraryName ValueObject
- events.py: Domain events

Consumers should only import from this __init__.py, not from submodules:
  ✅ GOOD:   from library.domain import Library, LibraryName
  ❌ BAD:    from library.domain.library import Library

Cross-Reference:
- DDD_RULES.yaml: library domain definition
- HEXAGONAL_RULES.yaml: Part 1, Domain layer constraints
- ADR-001: Independent Aggregate Roots
"""

# ============================================================================
# Public API - Aggregate Root
# ============================================================================

from .library import Library

__all_aggregates__ = [
    "Library",
]

# ============================================================================
# Public API - Value Objects
# ============================================================================

from .library_name import LibraryName

__all_values__ = [
    "LibraryName",
]

# ============================================================================
# Public API - Domain Events
# ============================================================================

from .events import (
    LibraryCreated,
    LibraryRenamed,
    LibraryDeleted,
    BasementCreated,
    LIBRARY_EVENTS,
)

__all_events__ = [
    "LibraryCreated",
    "LibraryRenamed",
    "LibraryDeleted",
    "BasementCreated",
    "LIBRARY_EVENTS",
]

# ============================================================================
# Consolidated Public API
# ============================================================================

__all__ = __all_aggregates__ + __all_values__ + __all_events__

"""
Module Exports Summary:

Aggregate Roots (Domain Objects):
  - Library: Top-level container per user (RULE-001)

Value Objects (Immutable, Validated):
  - LibraryName: Name validation (RULE-003)

Domain Events (State Changes):
  - LibraryCreated: New library created + basement auto-created
  - LibraryRenamed: Name changed
  - LibraryDeleted: Soft delete
  - BasementCreated: Basement recycle bin created

Consumer Usage:
  from library.domain import Library, LibraryName, LibraryCreated

  # Domain layer usage (pure logic)
  library = Library.create(user_id=user_id, name="My Library")
  library.rename("New Name")
  library.mark_deleted()

  # Service layer usage (business orchestration)
  for event in library.events:
      eventbus.publish(event)

  # Repository layer usage (persistence)
  await repository.save(library)  # ORM Model created from Library
"""