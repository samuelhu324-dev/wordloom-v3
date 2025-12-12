"""Tag domain layer exports

Pure domain logic with zero infrastructure dependencies.
Organized as:
- tag.py: AggregateRoot (Tag) + ValueObject (TagAssociation)
- events.py: 6 DomainEvents
- exceptions.py: 8 domain-specific exceptions
- enums.py: EntityType enum
"""

# Aggregate Root
from .tag import Tag, TagAssociation, DEFAULT_COLOR

# Domain Events
from .events import (
    TagCreated,
    TagRenamed,
    TagColorChanged,
    TagDeleted,
    TagAssociatedWithEntity,
    TagDisassociatedFromEntity,
)

# Domain Exceptions
from .exceptions import (
    TagNotFoundError,
    TagAlreadyExistsError,
    TagInvalidNameError,
    TagInvalidColorError,
    TagInvalidHierarchyError,
    TagAlreadyDeletedError,
    TagAssociationError,
    InvalidEntityTypeError,
)

# Enums
from .enums import EntityType

__all__ = [
    # Aggregate Root & Value Objects
    "Tag",
    "TagAssociation",
    "DEFAULT_COLOR",
    # Events
    "TagCreated",
    "TagRenamed",
    "TagColorChanged",
    "TagDeleted",
    "TagAssociatedWithEntity",
    "TagDisassociatedFromEntity",
    # Exceptions
    "TagNotFoundError",
    "TagAlreadyExistsError",
    "TagInvalidNameError",
    "TagInvalidColorError",
    "TagInvalidHierarchyError",
    "TagAlreadyDeletedError",
    "TagAssociationError",
    "InvalidEntityTypeError",
    # Enums
    "EntityType",
]
