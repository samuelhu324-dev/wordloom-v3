"""
Block Models - SQLAlchemy ORM definitions

Purpose:
- Define database schema for Block aggregate
- Support fractional index ordering (DECIMAL type)
- Support soft delete pattern
- Map ORM ↔ Domain model

Schema Changes (Phase 8):
- order: INT → NUMERIC(19,10) (Fractional Index support)
- Removed: title_text, title_level columns
- Added: heading_level (for HEADING type blocks only)
- Added: soft_deleted_at (for soft delete pattern)
- Renamed: block_type → type
"""

from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from core.database import Base


class BlockModel(Base):
    """Block ORM model"""

    __tablename__ = "blocks"

    # Primary key and foreign keys
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True)

    # Block type and content
    type = Column(String(50), nullable=False)  # BlockType enum: TEXT, HEADING, CODE, IMAGE, etc.
    content = Column(Text, nullable=False)  # Main content

    # Fractional index ordering (O(1) drag/drop operations)
    order = Column(Numeric(precision=19, scale=10), nullable=False, default=0)  # Decimal for fractional indexing

    # HEADING-specific field (only set when type='heading')
    heading_level = Column(Integer, nullable=True)  # 1, 2, or 3 for H1-H3

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    soft_deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete timestamp
