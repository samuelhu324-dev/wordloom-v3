"""Block Schemas"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional

class BlockCreate(BaseModel):
    block_type: str = Field(..., description="Block type: text, heading_1-3, image, code, etc.")
    content: str = Field(..., min_length=1, max_length=10000)
    order: int = Field(0, ge=0)

class BlockUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    order: Optional[int] = Field(None, ge=0)

class BlockResponse(BaseModel):
    id: UUID
    book_id: UUID
    block_type: str
    content: str
    order: int
    title_level: Optional[int] = None
    title_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
