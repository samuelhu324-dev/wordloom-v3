"""
Domain-Driven Design base classes - AggregateRoot, ValueObject, DomainEvent

Core DDD concepts:
- ValueObject: Immutable, identified by value, no identity
- DomainEvent: Records what happened, used for event sourcing
- AggregateRoot: Entity with identity, enforces invariants, publishes events

These are the foundation for all domain models in the system.
"""

from abc import ABC
from typing import List, Any
from datetime import datetime, timezone
from uuid import UUID


class ValueObject(ABC):
    """
    Base class for Value Objects

    Characteristics:
    - No identity (immutable)
    - Compared by value, not reference
    - No database id column
    - Used within Aggregates to represent domain concepts

    Example:
        class Color(ValueObject):
            def __init__(self, hex_code: str):
                self.hex_code = hex_code

        c1 = Color("#FF0000")
        c2 = Color("#FF0000")
        assert c1 == c2  # True (value comparison)
    """

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class DomainEvent(ABC):
    """
    Base class for Domain Events

    Characteristics:
    - Records something that happened in the domain
    - Immutable (happened in the past)
    - Timestamp indicates when event occurred
    - Published via EventBus for side effects (cascade updates, notifications)
    - Part of event sourcing pattern

    Example:
        class BookCreatedEvent(DomainEvent):
            def __init__(self, book_id: UUID, title: str):
                super().__init__()
                self.book_id = book_id
                self.title = title

        # In aggregate:
        event = BookCreatedEvent(book.id, book.title)
        book.add_event(event)
    """

    occurred_at: datetime

    def __init__(self):
        self.occurred_at = datetime.now(timezone.utc)


class AggregateRoot(ABC):
    """
    Base class for Aggregate Roots

    Characteristics:
    - Has identity (UUID)
    - Contains value objects and entities
    - Enforces invariants within aggregate boundary
    - Publishes domain events when state changes
    - Responsible for transaction consistency
    - Independent aggregate roots (not nested)

    Responsibilities:
    1. Enforce domain invariants
    2. Publish domain events
    3. Maintain consistency boundary
    4. No direct references between aggregates (use IDs)

    Example:
        class Book(AggregateRoot):
            def __init__(self, id: UUID, title: str, author: str):
                super().__init__(id)
                self.title = title
                self.author = author

            @staticmethod
            def create(title: str, author: str):
                book_id = uuid4()
                book = Book(book_id, title, author)
                book.add_event(BookCreatedEvent(book.id, book.title))
                return book
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    _events: List[DomainEvent] = []

    def __init__(self, id: UUID):
        self.id = id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self._events = []

    def add_event(self, event: DomainEvent) -> None:
        """
        Add event to pending events

        Events will be published to EventBus after persistence.
        Called after domain logic completes successfully.

        Args:
            event: DomainEvent instance to add
        """
        self._events.append(event)

    def get_events(self) -> List[DomainEvent]:
        """
        Get all pending events

        Returns:
            List[DomainEvent]: Copy of pending events
        """
        return self._events.copy()

    def clear_events(self) -> None:
        """
        Clear pending events

        Called by repository after saving to database and publishing events.
        Ensures events are not replayed on subsequent saves.
        """
        self._events.clear()


from abc import ABC
from typing import List, Any
from datetime import datetime, timezone
from uuid import UUID


class ValueObject(ABC):
    """
    Base class for Value Objects

    Characteristics:
    - No identity (immutable)
    - Compared by value, not reference
    - No database id column
    """

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class DomainEvent(ABC):
    """
    Base class for Domain Events

    Characteristics:
    - Records something that happened in domain
    - Immutable (occurred in past)
    - Timestamp indicates when event occurred
    - Can be published to event bus for side effects
    """

    occurred_at: datetime

    def __init__(self):
        self.occurred_at = datetime.now(timezone.utc)


class AggregateRoot(ABC):
    """
    Base class for Aggregate Roots

    Characteristics:
    - Has identity (UUID)
    - Contains value objects and entities
    - Enforces invariants within aggregate boundary
    - Publishes domain events when state changes
    - Responsible for transaction consistency
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    _events: List[DomainEvent] = []

    def __init__(self, id: UUID):
        self.id = id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self._events = []

    def add_event(self, event: DomainEvent) -> None:
        """Add event to pending events (will be published on save)"""
        self._events.append(event)

    def get_events(self) -> List[DomainEvent]:
        """Get all pending events"""
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear pending events (called after saving to database)"""
        self._events.clear()
