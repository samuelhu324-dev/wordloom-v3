"""Media Schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class MediaCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    file_url: str
    file_size: int = Field(..., ge=0)
    mime_type: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None

class MediaResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    file_url: str
    file_size: int
    mime_type: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
