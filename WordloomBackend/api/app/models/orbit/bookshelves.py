"""
Orbit Bookshelf 模型：书橱/分类管理

一个 Bookshelf 可包含多个 Notes，用于组织和管理 Notes
"""
from __future__ import annotations
from sqlalchemy import Column, Text, Integer, DateTime, func, text, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database_orbit import OrbitBase


class OrbitBookshelf(OrbitBase):
    """书橱实体：组织和分类 Notes"""

    __tablename__ = "orbit_bookshelves"

    id = Column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))

    # 基础信息
    name = Column(Text, nullable=False, index=True)  # 书橱名称
    description = Column(Text, nullable=True, default="")  # 描述
    cover_url = Column(Text, nullable=True)  # 封面图 URL
    icon = Column(Text, nullable=True)  # 可选：小图标（如 Lucide 图标名）

    # 优先级和紧急度
    priority = Column(Integer, nullable=False, server_default=text("3"))  # 优先级 1-5
    urgency = Column(Integer, nullable=False, server_default=text("3"))  # 紧急度 1-5

    # 统计数据
    usage_count = Column(Integer, nullable=False, server_default=text("0"))  # 使用次数
    note_count = Column(Integer, nullable=False, server_default=text("0"))  # Notes 数量（冗余但查询快）

    # 状态管理
    status = Column(Text, nullable=False, server_default=text("'active'"))  # active | archived | deleted
    is_favorite = Column(Boolean, nullable=False, server_default=text("false"))  # 收藏标记

    # 分类标签
    tags = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))

    # 主题色（可选）
    color = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系：一个 Bookshelf 包含多个 Notes
    notes = relationship(
        "OrbitNote",
        back_populates="bookshelf",
        foreign_keys="OrbitNote.bookshelf_id",
        cascade="save-update, merge",
        lazy="select"
    )

    def __repr__(self):
        return f"<OrbitBookshelf(id={self.id}, name={self.name}, note_count={self.note_count})>"
