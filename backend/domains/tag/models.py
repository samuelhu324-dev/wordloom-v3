"""Tag Models"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from core.database import Base

class TagModel(Base):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), default="#808080")
    icon = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class BookTagModel(Base):
    """N:M relationship between Books and Tags"""
    __tablename__ = "book_tags"
    book_id = Column(UUID(as_uuid=True), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
