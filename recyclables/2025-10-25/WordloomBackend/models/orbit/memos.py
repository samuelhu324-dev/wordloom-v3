# app/models/orbit/memos.py
# Orbit 模块 - Memo 模型定义

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.models.core import Base

class Memo(Base):
    __tablename__ = "memos"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    tags = Column(String(300), nullable=True)
    linked_source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    linked_entry_id = Column(Integer, ForeignKey("entries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    linked_source = relationship("Source", lazy="joined", uselist=False)
    linked_entry = relationship("Entry", lazy="joined", uselist=False)

    __table_args__ = (Index("ix_memos_created_at", "created_at"),)
