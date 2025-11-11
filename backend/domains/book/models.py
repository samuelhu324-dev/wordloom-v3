"""Book Models - SQLAlchemy ORM models"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from core.database import Base

class BookModel(Base):
    """Book ORM Model"""
    __tablename__ = "books"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bookshelf_id = Column(UUID(as_uuid=True), ForeignKey("bookshelves.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    is_pinned = Column(Boolean, default=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="draft")
    block_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BookModel(id={self.id}, title={self.title})>"
