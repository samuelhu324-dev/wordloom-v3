"""
Bookshelf Models - SQLAlchemy ORM models for persistence
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from core.database import Base


class BookshelfModel(Base):
    """Bookshelf ORM Model"""
    __tablename__ = "bookshelves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    library_id = Column(UUID(as_uuid=True), ForeignKey("libraries.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_pinned = Column(Boolean, default=False, nullable=False)
    pinned_at = Column(DateTime(timezone=True), nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    book_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<BookshelfModel(id={self.id}, library_id={self.library_id}, name={self.name})>"
