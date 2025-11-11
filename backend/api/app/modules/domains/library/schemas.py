"""
Library Schemas - Pydantic models for API validation and serialization

Used for:
- Request/response validation in FastAPI
- Serialization of Domain models
- Documentation generation
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class LibraryCreate(BaseModel):
    """Schema for creating a new Library"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Library name",
    )

    @validator("name")
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Library name cannot be empty")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "name": "My Personal Library"
            }
        }


class LibraryUpdate(BaseModel):
    """Schema for updating Library"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New Library name",
    )

    @validator("name")
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Library name cannot be empty")
        return v.strip() if v else None

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Library Name"
            }
        }


class LibraryResponse(BaseModel):
    """Schema for Library response"""
    id: UUID = Field(..., description="Library ID")
    user_id: UUID = Field(..., description="User ID who owns this Library")
    name: str = Field(..., description="Library name")
    created_at: datetime = Field(..., description="When Library was created")
    updated_at: datetime = Field(..., description="When Library was last updated")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "My Personal Library",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        }


class LibraryDetailResponse(LibraryResponse):
    """Detailed Library response (includes metadata)"""
    bookshelf_count: int = Field(0, description="Number of Bookshelves")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "My Personal Library",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "bookshelf_count": 5,
            }
        }
