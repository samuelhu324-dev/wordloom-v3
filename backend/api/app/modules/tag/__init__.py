"""Tag Module - Global tagging system

Exports:
- domain: Tag, TagAssociation, EntityType, and domain events
- service: TagService business logic
- repository: TagRepository interface and SQLAlchemyTagRepository implementation
- exceptions: All domain exceptions with HTTP status mapping
- schemas: Pydantic request/response models
- router: FastAPI endpoints
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

from .service import TagService
from .repository import TagRepository, SQLAlchemyTagRepository
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
from .router import router

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
    # Service
    "TagService",
    # Repository
    "TagRepository",
    "SQLAlchemyTagRepository",
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
    # Router
    "router",
]
