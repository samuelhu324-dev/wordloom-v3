"""Pydantic schemas for Basement HTTP layer."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MoveBookToBasementRequest(BaseModel):
    basement_bookshelf_id: UUID = Field(..., description="Target Basement bookshelf id")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional audit reason that will be captured with the operation",
    )


class RestoreBookFromBasementRequest(BaseModel):
    target_bookshelf_id: Optional[UUID] = Field(
        None,
        description="Destination bookshelf; defaults to previous bookshelf if omitted",
    )


class BasementBookResponse(BaseModel):
    id: UUID
    library_id: UUID
    bookshelf_id: UUID
    previous_bookshelf_id: Optional[UUID] = None
    title: str
    summary: Optional[str] = None
    status: str
    block_count: int = 0
    moved_to_basement_at: Optional[datetime] = None
    soft_deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class BasementBookListResponse(BaseModel):
    items: list[BasementBookResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
