"""Block Models"""
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from core.database import Base

class BlockModel(Base):
    __tablename__ = "blocks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True)
    block_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    title_level = Column(Integer, nullable=True)
    title_text = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
