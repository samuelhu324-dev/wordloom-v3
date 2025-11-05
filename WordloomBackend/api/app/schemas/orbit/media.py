"""
Media Resource 相关的 Pydantic 模式
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
import enum


class MediaEntityType(str, enum.Enum):
    """媒体资源实体类型"""
    BOOKSHELF_COVER = "bookshelf_cover"
    NOTE_COVER = "note_cover"
    CHECKPOINT_MARKER = "checkpoint_marker"
    IMAGE_BLOCK = "image_block"
    OTHER_BLOCK = "other_block"


class MediaResourceCreate(BaseModel):
    """创建媒体资源的输入"""
    workspace_id: UUID
    entity_type: MediaEntityType
    entity_id: UUID
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    display_order: Optional[int] = 0
    is_thumbnail: Optional[bool] = False


class MediaResourceUpdate(BaseModel):
    """更新媒体资源的输入"""
    display_order: Optional[int] = None
    is_thumbnail: Optional[bool] = None


class MediaResourceResponse(BaseModel):
    """媒体资源的输出"""
    id: UUID
    workspace_id: UUID
    entity_type: MediaEntityType
    entity_id: UUID
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    display_order: int
    is_thumbnail: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MediaResourceDeleteRequest(BaseModel):
    """删除媒体资源的输入"""
    media_id: UUID


class MediaResourceReorderRequest(BaseModel):
    """重新排列媒体资源的输入"""
    entity_id: UUID
    entity_type: MediaEntityType
    order: list[UUID]  # 新的排列顺序 (media_id 列表)
