"""Media Router HTTP Schemas

These schemas belong to the HTTP adapter layer (routers).
They should NOT be reused as application input commands.

Rationale:
- The module-level file api.app.modules.media.schemas.py contains legacy/REST schemas
  that don't match the current media_router endpoints.
- This file defines the exact HTTP contract used by media_router.py.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UploadImageQuery(BaseModel):
    description: Optional[str] = Field(None, description="Optional image description")


class UploadVideoQuery(BaseModel):
    description: Optional[str] = Field(None, description="Optional video description")


class UpdateMediaMetadataBody(BaseModel):
    width: Optional[int] = Field(None, ge=1, le=8000, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, le=8000, description="Image height in pixels")
    duration_ms: Optional[int] = Field(None, ge=1, le=7200000, description="Video duration in milliseconds")


class AssociateMediaQuery(BaseModel):
    entity_type: str = Field(..., description="Entity type (book, block, bookshelf, etc.)")
    entity_id: UUID = Field(..., description="Entity ID")


class DisassociateMediaQuery(BaseModel):
    entity_type: str = Field(..., description="Entity type (book, block, bookshelf, etc.)")
    entity_id: UUID = Field(..., description="Entity ID")


class PurgeMediaQuery(BaseModel):
    force: bool = Field(False, description="Force purge even if not in trash")


class MediaCreatedResponse(BaseModel):
    id: UUID
    filename: str
    storage_key: str
    mime_type: str
    media_type: str
    file_size: int


class ErrorResponse(BaseModel):
    detail: str
