"""Tag domain-specific exceptions - Business error hierarchy

RULE-018: Tag Creation & Management
RULE-019: Tag-Entity Association

All exceptions inherit from BusinessError base class.
Mapped to HTTP status codes in router layer.
"""

from typing import Optional
from uuid import UUID

from shared.errors import BusinessError


class TagNotFoundError(BusinessError):
    """Tag with given ID does not exist."""
    status_code = 404
    error_code = "TAG_NOT_FOUND"
    message = "Tag not found"

    def __init__(self, tag_id: UUID, detail: Optional[str] = None):
        self.tag_id = tag_id
        self.detail = detail or f"Tag {tag_id} does not exist"
        super().__init__(self.message, self.detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "tag_id": str(self.tag_id),
            "detail": self.detail
        }


class TagAlreadyExistsError(BusinessError):
    """Tag with given name already exists."""
    status_code = 409
    error_code = "TAG_ALREADY_EXISTS"
    message = "Tag name already exists"

    def __init__(self, name: str, detail: Optional[str] = None):
        self.name = name
        self.detail = detail or f"Tag with name '{name}' already exists"
        super().__init__(self.message, self.detail)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "name": self.name,
            "detail": self.detail
        }


class TagInvalidNameError(BusinessError):
    """Tag name violates validation rules (empty, too long, etc.)."""
    status_code = 422
    error_code = "TAG_INVALID_NAME"
    message = "Invalid tag name"

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(self.message, reason)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "name": self.name,
            "reason": self.reason
        }


class TagInvalidColorError(BusinessError):
    """Tag color violates validation rules (not hex, invalid format)."""
    status_code = 422
    error_code = "TAG_INVALID_COLOR"
    message = "Invalid tag color"

    def __init__(self, color: str, reason: str = "Color must be hex format (#RRGGBB or #RRGGBBAA)"):
        self.color = color
        self.reason = reason
        super().__init__(self.message, reason)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "color": self.color,
            "reason": self.reason
        }


class TagInvalidHierarchyError(BusinessError):
    """Tag hierarchy violates rules (cycle detected, max depth exceeded, parent not found)."""
    status_code = 422
    error_code = "TAG_INVALID_HIERARCHY"
    message = "Invalid tag hierarchy"

    def __init__(self, tag_id: UUID, reason: str):
        self.tag_id = tag_id
        self.reason = reason
        super().__init__(self.message, reason)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "tag_id": str(self.tag_id),
            "reason": self.reason
        }


class TagAlreadyDeletedError(BusinessError):
    """Tag is already soft-deleted and cannot be modified."""
    status_code = 409
    error_code = "TAG_ALREADY_DELETED"
    message = "Tag is already deleted"

    def __init__(self, tag_id: UUID):
        self.tag_id = tag_id
        super().__init__(self.message, f"Tag {tag_id} is already deleted")

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "tag_id": str(self.tag_id)
        }


class TagAssociationError(BusinessError):
    """Error in tag-entity association or disassociation."""
    status_code = 422
    error_code = "TAG_ASSOCIATION_ERROR"
    message = "Tag association error"

    def __init__(self, tag_id: UUID, entity_id: UUID, reason: str):
        self.tag_id = tag_id
        self.entity_id = entity_id
        self.reason = reason
        super().__init__(self.message, reason)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "tag_id": str(self.tag_id),
            "entity_id": str(self.entity_id),
            "reason": self.reason
        }


class InvalidEntityTypeError(BusinessError):
    """Entity type is not valid for tagging (must be BOOKSHELF, BOOK, BLOCK)."""
    status_code = 422
    error_code = "INVALID_ENTITY_TYPE"
    message = "Invalid entity type"

    def __init__(self, entity_type: str):
        self.entity_type = entity_type
        reason = f"Entity type must be one of: BOOKSHELF, BOOK, BLOCK (got '{entity_type}')"
        super().__init__(self.message, reason)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "entity_type": self.entity_type,
            "valid_types": ["BOOKSHELF", "BOOK", "BLOCK"]
        }
