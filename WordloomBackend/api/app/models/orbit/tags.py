"""
Orbit Tags Models - SQLAlchemy 模型定义

包含：
- OrbitTag: 标签表
- OrbitNoteTag: Note-Tag 关联表
"""

from __future__ import annotations
from sqlalchemy import Column, Text, Integer, DateTime, func, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database_orbit import OrbitBase


class OrbitTag(OrbitBase):
    """标签表 - 存储所有标签信息"""
    __tablename__ = "orbit_tags"

    id = Column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(Text, nullable=False, unique=True, index=True)
    color = Column(Text, nullable=False, server_default=text("'#808080'"))  # 默认灰色
    icon = Column(Text, nullable=True)  # Lucide 图标名
    description = Column(Text, nullable=True)
    count = Column(Integer, nullable=False, server_default=text("0"))  # 使用次数缓存

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系映射
    notes = relationship(
        "OrbitNote",
        secondary="orbit_note_tags",
        back_populates="tags_rel"
    )

    def __repr__(self):
        return f"<OrbitTag(id={self.id}, name={self.name}, count={self.count})>"


class OrbitNoteTag(OrbitBase):
    """Note-Tag 关联表 - 存储 Note 和 Tag 的多对多关系"""
    __tablename__ = "orbit_note_tags"

    note_id = Column(UUID(as_uuid=False), ForeignKey("orbit_notes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=False), ForeignKey("orbit_tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<OrbitNoteTag(note_id={self.note_id}, tag_id={self.tag_id})>"
