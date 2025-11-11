"""
Shared Base Classes - Foundation for all Domain models

Provides:
- AggregateRoot base class
- Entity base class
- ValueObject base class
- DomainEvent base class
- Repository interfaces
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


# ============================================================================
# Event Store
# ============================================================================

@dataclass
class DomainEvent(ABC):
    """
    Base class for all Domain Events

    Domain Events represent something that happened in the past within the domain.
    They are immutable and represent facts about the business.

    Usage:
        - Emit when aggregate state changes
        - Used for event sourcing
        - Used for pub/sub messaging (event bus)
        - Used for audit trail
    """

    @property
    def aggregate_id(self) -> UUID:
        """Get the ID of the aggregate that produced this event"""
        raise NotImplementedError

    @property
    def occurred_at(self) -> datetime:
        """Get when this event occurred"""
        raise NotImplementedError


# ============================================================================
# Entity Types
# ============================================================================

class ValueObject(ABC):
    """
    Base class for Value Objects

    Value Objects:
    - Have no identity (identity-less)
    - Are immutable
    - Are compared by value, not by reference
    - Examples: Money, Color, Range, Email

    Usage:
        @dataclass(frozen=True)
        class Email(ValueObject):
            value: str

            def __post_init__(self):
                if '@' not in self.value:
                    raise ValueError("Invalid email")
    """
    pass


class Entity(ABC):
    """
    Base class for Entities

    Entities:
    - Have unique identity
    - Mutable (state can change)
    - Compared by ID, not by value

    Usage:
        class User(Entity):
            id: UUID
            name: str
            email: str

            def change_name(self, new_name: str):
                self.name = new_name
    """

    @property
    def identity(self) -> UUID:
        raise NotImplementedError


class AggregateRoot(Entity):
    """
    Base class for Aggregate Roots

    Aggregate Roots:
    - Are entities with special responsibilities
    - Control access to other entities (aggregates)
    - Enforce business rules and invariants
    - Can emit domain events
    - Are persisted as atomic units

    Responsibilities:
    - Maintain aggregate consistency
    - Emit domain events
    - Provide business methods (not just getters/setters)

    Usage:
        class Order(AggregateRoot):
            def __init__(self, order_id, customer_id):
                self.id = order_id
                self.customer_id = customer_id
                self.events = []

            def add_item(self, item):
                # Enforce business rule
                if len(self.items) >= 10:
                    raise ValueError("Too many items")

                self.items.append(item)
                self.emit(ItemAdded(...))

            def emit(self, event: DomainEvent):
                self.events.append(event)
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    events: List[DomainEvent] = field(default_factory=list)

    @property
    def identity(self) -> UUID:
        return self.id

    def emit(self, event: DomainEvent) -> None:
        """
        Emit a domain event

        Args:
            event: DomainEvent to emit

        Side Effects:
            - Appends event to self.events
            - In production, may publish to event bus
        """
        self.events.append(event)

    def clear_events(self) -> List[DomainEvent]:
        """
        Clear and return all uncommitted events

        Used for:
        - Event sourcing (store events)
        - Pub/sub messaging (publish events)
        - Audit trail (log events)

        Returns:
            List of events that have been emitted since last clear
        """
        events = self.events[:]
        self.events = []
        return events


# ============================================================================
# Repository Interfaces
# ============================================================================

class IRepository(ABC):
    """
    Generic Repository interface

    Repository Pattern:
    - Mediates between domain and data mapping layers
    - Acts like an in-memory collection of aggregates
    - Abstracts persistence details from domain

    For each aggregate type, create a concrete repository:
        class LibraryRepository(IRepository):
            async def save(self, library: Library): ...
            async def get_by_id(self, library_id: UUID): ...
            async def delete(self, library_id: UUID): ...
    """

    @abstractmethod
    async def save(self, aggregate: AggregateRoot) -> None:
        """Save an aggregate (insert or update)"""
        pass

    @abstractmethod
    async def get_by_id(self, aggregate_id: UUID) -> Optional[AggregateRoot]:
        """Get an aggregate by ID"""
        pass

    @abstractmethod
    async def delete(self, aggregate_id: UUID) -> None:
        """Delete an aggregate"""
        pass


class IUnitOfWork(ABC):
    """
    Unit of Work pattern interface

    Unit of Work:
    - Maintains a list of objects affected by business transaction
    - Coordinates writing of changes to data source
    - Commits or rolls back all changes atomically

    Usage:
        async with UnitOfWork() as uow:
            library = await uow.libraries.get_by_id(lib_id)
            library.rename("New Name")
            await uow.commit()  # All changes committed atomically
    """

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes"""
        pass

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# ============================================================================
# Exception Base
# ============================================================================

class DomainException(Exception):
    """Base exception for all domain-specific exceptions"""
    pass


class BusinessRuleException(DomainException):
    """Exception for violated business rules and invariants"""
    pass


class AggregateNotFoundException(DomainException):
    """Exception when aggregate not found"""
    pass
