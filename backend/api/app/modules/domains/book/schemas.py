"""Book Schemas"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=1000)

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=1000)
    due_at: Optional[datetime] = None

class BookResponse(BaseModel):
    id: UUID
    bookshelf_id: UUID
    title: str
    summary: Optional[str] = None
    is_pinned: bool
    due_at: Optional[datetime] = None
    status: str
    block_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
