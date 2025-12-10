"""
Checkpoint 相关的 Pydantic 模式
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# ============================================================================
# Marker 图片对象
# ============================================================================

class CheckpointMarkerImageData(BaseModel):
    """Marker 的图片对象"""
    url: str  # 图片 URL


# ============================================================================
# Marker 模式
# ============================================================================

class CheckpointMarkerCreate(BaseModel):
    """创建 Marker 的输入"""
    title: str
    description: Optional[str] = None
    started_at: datetime
    ended_at: datetime
    category: Optional[str] = "work"  # work, pause, bug, feature, review, custom
    tags: Optional[List[str]] = None  # tag IDs
    color: Optional[str] = "#3b82f6"
    emoji: Optional[str] = "✓"
    order: Optional[int] = 0
    is_completed: Optional[bool] = False
    image_urls: Optional[List[CheckpointMarkerImageData]] = None  # 图片列表（最多 5 张）


class CheckpointMarkerUpdate(BaseModel):
    """更新 Marker 的输入"""
    title: Optional[str] = None
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None
    emoji: Optional[str] = None
    order: Optional[int] = None
    is_completed: Optional[bool] = None
    image_urls: Optional[List[CheckpointMarkerImageData]] = None  # 图片列表


class CheckpointMarkerResponse(BaseModel):
    """Marker 的输出"""
    id: UUID
    checkpoint_id: UUID
    title: str
    description: Optional[str]
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    category: str
    tags: List[str]
    color: str
    emoji: str
    order: int
    is_completed: bool
    image_urls: Optional[List[dict]] = None  # 改为 List[dict] 因为数据库返回的是 JSON 对象列表
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Checkpoint 模式
# ============================================================================

class CheckpointCreate(BaseModel):
    """创建 Checkpoint 的输入"""
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"  # pending, in_progress, on_hold, done
    tags: Optional[List[str]] = None  # tag IDs
    order: Optional[int] = 0


class CheckpointUpdate(BaseModel):
    """更新 Checkpoint 的输入"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    order: Optional[int] = None


class CheckpointResponse(BaseModel):
    """Checkpoint 的基础输出"""
    id: UUID
    note_id: UUID
    title: str
    description: Optional[str]
    status: str
    tags: List[str]
    order: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: int
    actual_work_seconds: int
    completion_percentage: float

    class Config:
        from_attributes = True


class CheckpointDetailResponse(CheckpointResponse):
    """Checkpoint 的详细输出（包括所有 marker）"""
    markers: List[CheckpointMarkerResponse]
