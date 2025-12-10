from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Column, Text, Integer, DateTime, func, text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database_orbit import OrbitBase

if TYPE_CHECKING:
    from app.models.orbit.bookshelves import OrbitBookshelf

class OrbitNote(OrbitBase):
    __tablename__ = "orbit_notes"

    id = Column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True, default="")  # 新增：Note 摘要/描述
    content_md = Column(Text, nullable=True, default="")
    blocks_json = Column(Text, nullable=True, default="[]")  # 新增：JSON格式的blocks数组
    preview_image = Column(Text, nullable=True, default=None)  # 新增：封面图 URL
    status = Column(Text, nullable=False, server_default=text("'open'"))
    priority = Column(Integer, nullable=False, server_default=text("3"))
    # 紧急程度 1-5
    urgency = Column(Integer, nullable=False, server_default=text("'3'"))
    usage_level = Column(Integer, nullable=False, server_default=text("'3'"))
    # 使用次数（自动计数，用户点击时递增）
    usage_count = Column(Integer, nullable=False, server_default=text("0"))
    tags = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))
    due_at = Column(DateTime(timezone=True), nullable=True)
    is_pinned = Column(Boolean, nullable=False, server_default=text("false"))  # 置顶标记
    pinned_at = Column(DateTime(timezone=True), nullable=True)  # 置顶时间

    # 业界标准：存储路径固定，不随 bookshelf 改变
    # 格式：relative/path/notes/{note_id}
    storage_path = Column(Text, nullable=False, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Bookshelf 关联（外键）- 只记录业务关系，不影响存储路径
    bookshelf_id = Column(UUID(as_uuid=False), ForeignKey("orbit_bookshelves.id", ondelete="SET NULL"), nullable=True, index=True)

    # 关系映射到新的标签系统
    tags_rel = relationship(
        "OrbitTag",
        secondary="orbit_note_tags",
        back_populates="notes"
    )

    # 关系映射到 Bookshelf（延迟加载，避免循环导入）
    bookshelf = relationship(
        "OrbitBookshelf",
        back_populates="notes",
        foreign_keys=[bookshelf_id],
        lazy="noload"  # 不自动加载，需要时显式查询
    )