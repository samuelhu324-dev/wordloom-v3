"""
Media Resources 的 ORM 模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database_orbit import OrbitBase


class MediaEntityType(enum.Enum):
    """媒体资源所属的实体类型"""
    BOOKSHELF_COVER = "bookshelf_cover"
    NOTE_COVER = "note_cover"
    CHECKPOINT_MARKER = "checkpoint_marker"
    IMAGE_BLOCK = "image_block"
    OTHER_BLOCK = "other_block"


class OrbitMediaResource(OrbitBase):
    """统一的媒体资源表"""
    __tablename__ = "media_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 所有权信息
    workspace_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(SQLEnum(MediaEntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    # 文件信息
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256，移除 unique=True

    # 图片元数据
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # 视频用

    # 排序和管理
    display_order = Column(Integer, default=0)
    is_thumbnail = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 软删除

    # 约束：同一实体的同一文件不能重复
    __table_args__ = (
        UniqueConstraint('entity_id', 'file_hash', name='unique_file_per_entity'),
    )
