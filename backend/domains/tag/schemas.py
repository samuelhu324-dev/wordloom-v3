"""Tag Schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field("#808080", regex="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

class TagResponse(BaseModel):
    id: UUID
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None
    count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
