"""
Bookshelf Schemas - Pydantic models for API validation
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class BookshelfCreate(BaseModel):
    """Schema for creating a new Bookshelf"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

    @validator("name")
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Bookshelf name cannot be empty")
        return v.strip()


class BookshelfUpdate(BaseModel):
    """Schema for updating Bookshelf"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class BookshelfResponse(BaseModel):
    """Schema for Bookshelf response"""
    id: UUID
    library_id: UUID
    name: str
    description: Optional[str] = None
    is_pinned: bool
    pinned_at: Optional[datetime] = None
    is_favorite: bool
    status: str
    book_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
