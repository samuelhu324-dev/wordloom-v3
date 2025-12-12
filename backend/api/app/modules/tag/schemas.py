"""Tag Schemas - Pydantic v2 DTOs for API validation

Strategy (ADR-025: Tag Schemas & Validation):
==============================================
- Request schemas for input validation (CreateTagRequest, UpdateTagRequest, etc.)
- Response schemas for output serialization (TagResponse, TagAssociationResponse, etc.)
- Pydantic v2 validation with Field constraints
- Nested schemas for hierarchical responses

Validation Rules (RULE-018/019/020):
✅ name: 1-50 chars, non-empty, unique
✅ color: hex format validation (#RRGGBB or #RRGGBBAA)
✅ icon: optional lucide icon name
✅ level: 0=top-level, 1+=subtags (auto-calculated)
✅ parent_tag_id: only for subtags, cannot form cycles
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class EntityTypeEnum(str, Enum):
    """Entity types that can be tagged"""
    LIBRARY = "library"
    BOOKSHELF = "bookshelf"
    BOOK = "book"
    BLOCK = "block"


# ============================================================================
# Request Schemas
# ============================================================================

class CreateTagRequest(BaseModel):
    """Request to create a new tag"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tag name (unique, 1-50 characters)"
    )
    color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description="Tag color in hex format (#RRGGBB or #RRGGBBAA). Optional: backend will default to gray."
    )
    icon: Optional[str] = Field(
        None,
        max_length=50,
        description="Lucide icon name (optional, e.g., bookmark, star)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python",
                "color": "#FF5733",
                "icon": "code",
                "description": "Python programming language"
            }
        }


class CreateSubtagRequest(BaseModel):
    """Request to create a hierarchical sub-tag"""

    parent_tag_id: Optional[UUID] = Field(
        None,
        description="(Deprecated) Parent tag ID. The API uses the path parameter as the source of truth."
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Sub-tag name"
    )
    color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description="Sub-tag color (optional; backend defaults to gray)"
    )
    icon: Optional[str] = Field(
        None,
        max_length=50,
        description="Lucide icon name (optional)"
    )

    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "parent_tag_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Django",
                "color": "#092E20",
                "icon": "framework",
                "description": "Web framework under Python"
            }
        }


class UpdateTagRequest(BaseModel):
    """Request to update tag properties"""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="New tag name"
    )
    color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description="New tag color"
    )
    icon: Optional[str] = Field(
        None,
        max_length=50,
        description="New icon"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="New description"
    )
    parent_tag_id: Optional[UUID] = Field(
        None,
        description="New parent tag id (use null to move to top-level)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python 3.12",
                "color": "#3776AB"
            }
        }


class AssociateTagRequest(BaseModel):
    """Request to associate a tag with an entity"""

    entity_type: EntityTypeEnum = Field(
        ...,
        description="Type of entity to tag (BOOKSHELF|BOOK|BLOCK)"
    )
    entity_id: UUID = Field(
        ...,
        description="ID of the entity to tag"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "book",
                "entity_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class TagResponse(BaseModel):
    """Response containing tag information"""

    id: UUID
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_tag_id: Optional[UUID] = None
    level: int = 0
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Python",
                "color": "#FF5733",
                "icon": "code",
                "description": "Python programming language",
                "parent_tag_id": None,
                "level": 0,
                "usage_count": 42,
                "created_at": "2025-11-13T12:00:00Z",
                "updated_at": "2025-11-13T12:00:00Z",
                "deleted_at": None
            }
        }


class TagHierarchyResponse(BaseModel):
    """Response with hierarchical structure (parent + subtags)"""

    id: UUID
    name: str
    color: str
    icon: Optional[str] = None
    level: int = 0
    usage_count: int = 0
    children: List["TagHierarchyResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Technology",
                "color": "#3776AB",
                "level": 0,
                "usage_count": 100,
                "children": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Python",
                        "color": "#FF5733",
                        "level": 1,
                        "usage_count": 42,
                        "children": []
                    }
                ]
            }
        }


class TagAssociationResponse(BaseModel):
    """Response containing tag-entity association info"""

    id: UUID
    tag_id: UUID
    entity_type: EntityTypeEnum
    entity_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tag_id": "550e8400-e29b-41d4-a716-446655440001",
                "entity_type": "book",
                "entity_id": "550e8400-e29b-41d4-a716-446655440002",
                "created_at": "2025-11-13T12:00:00Z"
            }
        }


class TagListResponse(BaseModel):
    """Response containing list of tags (with pagination)"""

    items: List[TagResponse]
    total: int
    page: int
    size: int
    has_more: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Python",
                        "color": "#FF5733",
                        "icon": "code",
                        "level": 0,
                        "usage_count": 42,
                        "created_at": "2025-11-13T12:00:00Z",
                        "updated_at": "2025-11-13T12:00:00Z",
                        "deleted_at": None
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 20,
                "has_more": False
            }
        }


class EntityTagsResponse(BaseModel):
    """Response containing all tags for a specific entity"""

    entity_type: EntityTypeEnum
    entity_id: UUID
    tags: List[TagResponse]
    count: int

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "book",
                "entity_id": "550e8400-e29b-41d4-a716-446655440000",
                "tags": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Python",
                        "color": "#FF5733",
                        "icon": "code",
                        "level": 0,
                        "usage_count": 42,
                        "created_at": "2025-11-13T12:00:00Z",
                        "updated_at": "2025-11-13T12:00:00Z",
                        "deleted_at": None
                    }
                ],
                "count": 1
            }
        }


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""

    code: str = Field(..., description="Error code (e.g., TAG_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    details: dict = Field(default_factory=dict, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "TAG_NOT_FOUND",
                "message": "Tag 550e8400-e29b-41d4-a716-446655440000 not found",
                "details": {"tag_id": "550e8400-e29b-41d4-a716-446655440000"}
            }
        }


# Update forward references for recursive models
TagHierarchyResponse.model_rebuild()
