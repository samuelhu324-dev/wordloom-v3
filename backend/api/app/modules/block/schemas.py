"""
Block Schemas - Request/Response DTOs for Block API

Implements Pydantic v2 with validation, DTO pattern, Decimal serialization, and pagination.
Maps to RULE-013-REVISED, RULE-014, RULE-015-REVISED, RULE-016, POLICY-008.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from enum import Enum
from decimal import Decimal


# ============================================================================
# Enums
# ============================================================================

class BlockTypeEnum(str, Enum):
    """Block type values (RULE-013-REVISED + RULE-014)"""
    TEXT = "text"
    HEADING = "heading"  # With heading_level (1-3)
    IMAGE = "image"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    LIST = "list"
    DIVIDER = "divider"


# ============================================================================
# Request Schemas (Input Validation)
# ============================================================================

class BlockCreate(BaseModel):
    """Create Block request (RULE-013-REVISED + RULE-014)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "block_type": "text",
                "content": "This is a text block with content",
                "order": "100.5"
            }
        }
    )

    block_type: BlockTypeEnum = Field(..., description="Type of block (text, heading, image, code, etc.)")
    content: str = Field(..., min_length=1, max_length=10000, description="Block content")
    order: str = Field(default="0", description="Fractional index for ordering (RULE-015)")
    heading_level: Optional[int] = Field(None, ge=1, le=3, description="1-3 for HEADING type (RULE-013)")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Strip and validate content"""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v.strip()

    @field_validator("heading_level")
    @classmethod
    def validate_heading_level(cls, v: Optional[int], info) -> Optional[int]:
        """Heading level only valid for HEADING type"""
        if v is not None and not (1 <= v <= 3):
            raise ValueError("Heading level must be 1, 2, or 3")

        # Check consistency with block_type
        data = info.data
        if data.get("block_type") == BlockTypeEnum.HEADING:
            if v is None:
                raise ValueError("heading_level is required for HEADING type")
        elif v is not None:
            raise ValueError(f"heading_level should only be set for HEADING type, not {data.get('block_type')}")

        return v

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: str) -> str:
        """Validate fractional index (RULE-015)"""
        try:
            order_decimal = Decimal(v)
            if order_decimal < 0 or order_decimal >= 1024:
                raise ValueError("Order must be between 0 and 1024")
        except (ValueError, TypeError):
            raise ValueError("Order must be a valid decimal number")
        return v


class BlockUpdate(BaseModel):
    """Update Block request"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "content": "Updated content",
                "order": "200.25"
            }
        }
    )

    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    order: Optional[str] = Field(None, description="Fractional index (RULE-015)")
    heading_level: Optional[int] = Field(None, ge=1, le=3)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v.strip() if v else None

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                order_decimal = Decimal(v)
                if order_decimal < 0 or order_decimal >= 1024:
                    raise ValueError("Order must be between 0 and 1024")
            except (ValueError, TypeError):
                raise ValueError("Order must be a valid decimal number")
        return v


class BlockReorderRequest(BaseModel):
    """Batch reorder blocks request (RULE-015: Fractional Index)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reorders": [
                    {"block_id": "550e8400-e29b-41d4-a716-446655440000", "order": "10.5"},
                    {"block_id": "550e8400-e29b-41d4-a716-446655440001", "order": "20.25"},
                ]
            }
        }
    )

    class ReorderItem(BaseModel):
        block_id: UUID
        order: str = Field(..., description="New fractional index")

        @field_validator("order")
        @classmethod
        def validate_order(cls, v: str) -> str:
            try:
                Decimal(v)
            except (ValueError, TypeError):
                raise ValueError("Order must be a valid decimal")
            return v

    reorders: List[ReorderItem] = Field(..., min_length=1, description="List of blocks to reorder")


# ============================================================================
# Response Schemas (Output Serialization)
# ============================================================================

class BlockDTO(BaseModel):
    """Internal Data Transfer Object (Service → Router layer)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    block_type: BlockTypeEnum
    content: str
    order: Decimal  # ← Internal Decimal representation
    heading_level: Optional[int] = None
    soft_deleted_at: Optional[datetime] = None
    # === NEW: Paperballs fields (Doc 8 Integration) ===
    deleted_prev_id: Optional[UUID] = None
    deleted_next_id: Optional[UUID] = None
    deleted_section_path: Optional[str] = None
    recovery_hint: Optional[str] = None  # "Level X: ..." for UI display
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, block_domain) -> "BlockDTO":
        """Convert Block domain object to DTO"""
        return cls(
            id=block_domain.id,
            book_id=block_domain.book_id,
            block_type=block_domain.type,
            content=block_domain.content.value,  # Value Object
            order=block_domain.order,
            heading_level=block_domain.heading_level,
            soft_deleted_at=getattr(block_domain, 'soft_deleted_at', None),
            # === NEW: Paperballs fields ===
            deleted_prev_id=getattr(block_domain, 'deleted_prev_id', None),
            deleted_next_id=getattr(block_domain, 'deleted_next_id', None),
            deleted_section_path=getattr(block_domain, 'deleted_section_path', None),
            recovery_hint=getattr(block_domain, 'recovery_hint', None),
            created_at=block_domain.created_at,
            updated_at=block_domain.updated_at,
        )

    def to_response(self) -> "BlockResponse":
        """Convert DTO to API response"""
        return BlockResponse(
            id=self.id,
            book_id=self.book_id,
            block_type=self.block_type,
            content=self.content,
            order=str(self.order),  # Serialize to string for JSON
            heading_level=self.heading_level,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_detail_response(self) -> "BlockDetailResponse":
        """Convert DTO to detailed API response"""
        return BlockDetailResponse(
            id=self.id,
            book_id=self.book_id,
            block_type=self.block_type,
            content=self.content,
            order=str(self.order),
            heading_level=self.heading_level,
            char_count=len(self.content),
            soft_deleted_at=self.soft_deleted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_deleted_response(self) -> "DeletedBlockDTO":
        """Convert DTO to deleted block response with recovery metadata"""
        return DeletedBlockDTO(
            id=self.id,
            book_id=self.book_id,
            block_type=self.block_type,
            content=self.content,
            order=str(self.order),
            heading_level=self.heading_level,
            soft_deleted_at=self.soft_deleted_at,
            # === Paperballs metadata ===
            deleted_prev_id=self.deleted_prev_id,
            deleted_next_id=self.deleted_next_id,
            deleted_section_path=self.deleted_section_path,
            recovery_hint=self.recovery_hint,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class BlockResponse(BaseModel):
    """Standard Block response (basic fields)"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "book_id": "550e8400-e29b-41d4-a716-446655440001",
                "block_type": "text",
                "content": "This is a text block",
                "order": "100.5",
                "heading_level": None,
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    id: UUID
    book_id: UUID
    block_type: BlockTypeEnum
    content: str
    order: str  # Serialized as string for JSON compatibility
    heading_level: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class BlockDetailResponse(BlockResponse):
    """Extended Block response with metadata"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "book_id": "550e8400-e29b-41d4-a716-446655440001",
                "block_type": "text",
                "content": "This is a text block",
                "order": "100.5",
                "heading_level": None,
                "char_count": 21,
                "soft_deleted_at": None,
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    char_count: int  # Content character count
    soft_deleted_at: Optional[datetime] = None  # POLICY-008: Soft delete indicator


class BlockPaginatedResponse(BaseModel):
    """Paginated Block list response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "page_size": 50,
                "has_more": False,
            }
        }
    )

    items: List[BlockDetailResponse]
    total: int = Field(..., ge=0, description="Total number of blocks")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size (1-100)")
    has_more: bool = Field(..., description="Whether more pages exist")


# ========== NEW: Paperballs Recovery Response Schemas (Doc 8 Integration) ==========

class DeletedBlockDTO(BaseModel):
    """Deleted Block response with Paperballs recovery metadata"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "book_id": "550e8400-e29b-41d4-a716-446655440001",
                "block_type": "text",
                "content": "This is a deleted text block",
                "order": "100.5",
                "heading_level": None,
                "soft_deleted_at": "2025-11-14T10:00:00Z",
                "deleted_prev_id": "550e8400-e29b-41d4-a716-446655440002",
                "deleted_next_id": None,
                "deleted_section_path": "introduction",
                "recovery_hint": "Level 1: 在前驱节点之后恢复",
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:00:00Z",
            }
        }
    )

    id: UUID
    book_id: UUID
    block_type: BlockTypeEnum
    content: str
    order: str
    heading_level: Optional[int] = None
    soft_deleted_at: datetime
    # === Paperballs recovery fields ===
    deleted_prev_id: Optional[UUID] = Field(None, description="Level 1 recovery reference")
    deleted_next_id: Optional[UUID] = Field(None, description="Level 2 recovery reference")
    deleted_section_path: Optional[str] = Field(None, description="Level 3 recovery reference")
    recovery_hint: Optional[str] = Field(None, description="Human-readable recovery strategy")
    # === Audit ===
    created_at: datetime
    updated_at: datetime


class ListDeletedBlocksResponse(BaseModel):
    """List deleted blocks response with recovery metadata"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "book_id": "550e8400-e29b-41d4-a716-446655440001",
                "deleted_blocks": [],
                "total_count": 5,
                "recovery_stats": {
                    "level_1": 2,
                    "level_2": 1,
                    "level_3": 1,
                    "level_4": 0
                }
            }
        }
    )

    book_id: UUID
    deleted_blocks: List[DeletedBlockDTO]
    total_count: int = Field(..., ge=0, description="Total deleted blocks")
    recovery_stats: dict = Field(
        default_factory=lambda: {"level_1": 0, "level_2": 0, "level_3": 0, "level_4": 0},
        description="Recovery strategy distribution across deleted blocks"
    )


class RestoreBlockResponse(BaseModel):
    """Block restoration response with recovery level information"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "book_id": "550e8400-e29b-41d4-a716-446655440001",
                "success": True,
                "recovery_level": 1,
                "new_order": "100.5",
                "message": "Block restored successfully at Level 1 (after previous sibling)"
            }
        }
    )

    id: UUID
    book_id: UUID
    success: bool = Field(..., description="Whether restoration succeeded")
    recovery_level: int = Field(..., ge=1, le=4, description="Recovery level used (1-4)")
    new_order: str = Field(..., description="New fractional index after restoration")
    message: str = Field(..., description="Human-readable restoration status")


class BlockErrorResponse(BaseModel):
    """Structured error response"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "code": "BLOCK_NOT_FOUND",
                "message": "Block not found: 550e8400-e29b-41d4-a716-446655440000",
                "details": {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "book_id": "550e8400-e29b-41d4-a716-446655440001",
                }
            }
        }
    )

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error context")
