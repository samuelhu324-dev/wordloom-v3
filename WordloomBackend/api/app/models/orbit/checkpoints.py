"""
Checkpoint 和 Marker 的 ORM 模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database_orbit import OrbitBase


class OrbitNoteCheckpoint(OrbitBase):
    """Note 内的检查点（子事项）"""
    __tablename__ = "orbit_note_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("orbit_notes.id", ondelete="CASCADE"), nullable=False)

    # 内容
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # 状态
    status = Column(String, default="pending")  # pending, in_progress, on_hold, done
    order = Column(Integer, default=0)

    # 时间
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 标签（存储 tag ID 列表）
    tags = Column(JSONB, default=list)

    # 关系
    markers = relationship("OrbitNoteCheckpointMarker", cascade="all, delete-orphan", order_by="OrbitNoteCheckpointMarker.order")

    @property
    def duration_seconds(self) -> int:
        """计算总工作时长（秒）- 所有非暂停 marker 的时长之和"""
        total = 0
        for marker in self.markers:
            if marker.category != "pause":
                total += marker.duration_seconds
        return total

    @property
    def actual_work_seconds(self) -> int:
        """计算实际工作时间（秒）- 等同于 duration_seconds"""
        return self.duration_seconds

    @property
    def completion_percentage(self) -> float:
        """计算完成度百分比"""
        if self.status == "done":
            return 100.0

        total_markers = len(self.markers)
        if total_markers == 0:
            return 0.0

        completed = sum(1 for m in self.markers if m.is_completed)
        return (completed / total_markers) * 100


class OrbitNoteCheckpointMarker(OrbitBase):
    """Checkpoint 内的标记（进度标记）"""
    __tablename__ = "orbit_note_checkpoint_markers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkpoint_id = Column(UUID(as_uuid=True), ForeignKey("orbit_note_checkpoints.id", ondelete="CASCADE"), nullable=False)

    # 内容
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # 时间
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, default=0)

    # 分类和标签
    category = Column(String, default="work")  # work, pause, bug, feature, review, custom
    tags = Column(JSONB, default=list)  # 存储 tag ID 列表

    # 完成状态
    is_completed = Column(Boolean, default=False)  # 标记是否已完成

    # 显示相关
    color = Column(String, default="#3b82f6")
    emoji = Column(String, default="✓")

    # 图片列表（最多 5 张，每张 60x60 固定大小）
    # 格式：[{"url": "..."}, {"url": "..."}, ...]
    image_urls = Column(JSONB, default=list)  # 图片 URL 列表

    # 排序和时间戳
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动计算 duration_seconds
        if self.started_at and self.ended_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
