from __future__ import annotations
from sqlalchemy import Column, Text, Integer, DateTime, func, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database_orbit import OrbitBase

class OrbitNote(OrbitBase):
    __tablename__ = "orbit_notes"

    id = Column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(Text, nullable=True)
    content_md = Column(Text, nullable=True, default="")
    status = Column(Text, nullable=False, server_default=text("'open'"))
    priority = Column(Integer, nullable=False, server_default=text("3"))
    # 紧急程度 1-5
    urgency = Column(Integer, nullable=False, server_default=text("'3'"))
    # 日用程度 1-5（避免使用关键字 usage，采用 usage_level）
    usage_level = Column(Integer, nullable=False, server_default=text("'3'"))
    # 使用次数（自动计数，用户点击时递增）
    usage_count = Column(Integer, nullable=False, server_default=text("0"))
    tags = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Bookshelf 关联（外键）
    bookshelf_id = Column(UUID(as_uuid=False), ForeignKey("orbit_bookshelves.id", ondelete="SET NULL"), nullable=True, index=True)

    # 关系映射到新的标签系统
    tags_rel = relationship(
        "OrbitTag",
        secondary="orbit_note_tags",
        back_populates="notes"
    )

    # 关系映射到 Bookshelf
    bookshelf = relationship(
        "OrbitBookshelf",
        back_populates="notes",
        foreign_keys=[bookshelf_id],
        lazy="select"
    )