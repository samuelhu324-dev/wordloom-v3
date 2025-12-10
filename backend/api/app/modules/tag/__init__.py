"""Tag Module - Global tagging system

Exports:
- domain: Tag, TagAssociation, EntityType, and domain events
- exceptions: All domain exceptions with HTTP status mapping
- schemas: Pydantic request/response models
"""

from .domain import (
    Tag,
    TagAssociation,
    EntityType,
    TagCreated,
    TagRenamed,
    TagColorChanged,
    TagDeleted,
    TagAssociatedWithEntity,
    TagDisassociatedFromEntity,
)

from .exceptions import (
    TagException,
    TagNotFoundError,
    TagAlreadyExistsError,
    TagInvalidNameError,
    TagInvalidColorError,
    TagInvalidHierarchyError,
    TagAlreadyAssociatedError,
    TagAssociationNotFoundError,
    TagAlreadyDeletedError,
    TagOperationError,
)
from .schemas import (
    CreateTagRequest,
    CreateSubtagRequest,
    UpdateTagRequest,
    AssociateTagRequest,
    TagResponse,
    TagHierarchyResponse,
    TagAssociationResponse,
    TagListResponse,
    EntityTagsResponse,
    ErrorResponse,
)

__all__ = [
    # Domain
    "Tag",
    "TagAssociation",
    "EntityType",
    "TagCreated",
    "TagRenamed",
    "TagColorChanged",
    "TagDeleted",
    "TagAssociatedWithEntity",
    "TagDisassociatedFromEntity",
    # Exceptions
    "TagException",
    "TagNotFoundError",
    "TagAlreadyExistsError",
    "TagInvalidNameError",
    "TagInvalidColorError",
    "TagInvalidHierarchyError",
    "TagAlreadyAssociatedError",
    "TagAssociationNotFoundError",
    "TagAlreadyDeletedError",
    "TagOperationError",
    # Schemas
    "CreateTagRequest",
    "CreateSubtagRequest",
    "UpdateTagRequest",
    "AssociateTagRequest",
    "TagResponse",
    "TagHierarchyResponse",
    "TagAssociationResponse",
    "TagListResponse",
    "EntityTagsResponse",
    "ErrorResponse",
]
