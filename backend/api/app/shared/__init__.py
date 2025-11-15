"""
Shared Layer - Common utilities, base classes, and DTOs

Exports:
- DDD base classes: AggregateRoot, ValueObject, DomainEvent (from base.py)
- Domain errors: BusinessError and all domain-specific errors (from errors.py)
- DTOs: PageResponse, ErrorResponse, BaseResponse (from schemas.py)
- Events: Event infrastructure (from events.py)
- Dependencies: Dependency injection utilities (from deps.py)
"""

from .base import AggregateRoot, ValueObject, DomainEvent
from .errors import BusinessError
from .schemas import PageResponse, ErrorResponse, BaseResponse
from .events import EventBus
from .deps import get_db

__all__ = [
    "AggregateRoot",
    "ValueObject",
    "DomainEvent",
    "BusinessError",
    "PageResponse",
    "ErrorResponse",
    "BaseResponse",
    "EventBus",
    "get_db",
]
