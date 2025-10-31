from __future__ import annotations
import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer

class BookmarkBase(BaseModel):
    title: str = ""
    text: str = ""
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    urgency: int = 3
    daily: int = 3
    status: str = "active"
    pinned: bool = False
    image_path: Optional[str] = None
    next_action: Optional[str] = None
    due_at: Optional[str] = None
    blocked_reason: Optional[str] = None
    snooze_until: Optional[str] = None

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None
    urgency: Optional[int] = None
    daily: Optional[int] = None
    status: Optional[str] = None
    pinned: Optional[bool] = None
    image_path: Optional[str] = None
    next_action: Optional[str] = None
    due_at: Optional[str] = None
    blocked_reason: Optional[str] = None
    snooze_until: Optional[str] = None

class BookmarkRead(BookmarkBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    @field_serializer("created_at", "updated_at", "done_at", "archived_at", when_used='json')
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True
