"""
Media Input Ports - UseCase Interfaces

定义所有 Media UseCase 的接口契约，供 Router 调用。

UseCase 接口设计原则:
1. 一个接口对应一个 UseCase
2. 方法名为 execute()
3. 参数使用 DTO 类（Input Request）
4. 返回值使用 DTO 类（Output Response）
5. 异常通过 Exception 抛出
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from ...domain import Media, MediaMimeType, EntityTypeForMedia


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class UploadImageRequest:
    """上传图片的请求"""
    filename: str
    mime_type: MediaMimeType
    file_size: int
    storage_key: str
    width: Optional[int] = None
    height: Optional[int] = None
    storage_quota: int = 1024 * 1024 * 1024  # 1GB
    used_storage: int = 0


@dataclass
class UploadVideoRequest:
    """上传视频的请求"""
    filename: str
    mime_type: MediaMimeType
    file_size: int
    storage_key: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    storage_quota: int = 1024 * 1024 * 1024  # 1GB
    used_storage: int = 0


@dataclass
class DeleteMediaRequest:
    """删除 Media 的请求"""
    media_id: UUID


@dataclass
class RestoreMediaRequest:
    """恢复 Media 的请求"""
    media_id: UUID


@dataclass
class PurgeMediaRequest:
    """硬删除 Media 的请求"""
    media_id: UUID


@dataclass
class AssociateMediaRequest:
    """关联 Media 到 Entity 的请求"""
    media_id: UUID
    entity_type: EntityTypeForMedia
    entity_id: UUID


@dataclass
class DisassociateMediaRequest:
    """移除 Media 与 Entity 关联的请求"""
    media_id: UUID
    entity_type: EntityTypeForMedia
    entity_id: UUID


@dataclass
class GetMediaRequest:
    """获取 Media 的请求"""
    media_id: UUID


@dataclass
class UpdateImageMetadataRequest:
    """更新图片元数据的请求"""
    media_id: UUID
    width: int
    height: int


@dataclass
class UpdateVideoMetadataRequest:
    """更新视频元数据的请求"""
    media_id: UUID
    duration_ms: int


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class MediaResponse:
    """Media 的响应 DTO"""
    id: UUID
    filename: str
    mime_type: str
    file_size: int
    storage_key: str
    width: Optional[int]
    height: Optional[int]
    duration_ms: Optional[int]
    state: str  # ACTIVE, IN_TRASH, PURGED
    trash_at: Optional[str]
    created_at: str

    @classmethod
    def from_domain(cls, media: Media) -> "MediaResponse":
        """从域对象转换"""
        return cls(
            id=media.id,
            filename=media.filename,
            mime_type=media.mime_type.value,
            file_size=media.file_size,
            storage_key=media.storage_key,
            width=media.width,
            height=media.height,
            duration_ms=media.duration_ms,
            state=media.state.value,
            trash_at=media.trash_at.isoformat() if media.trash_at else None,
            created_at=media.created_at.isoformat() if media.created_at else None
        )


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class UploadImageUseCase(ABC):
    """上传图片的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UploadImageRequest) -> MediaResponse:
        """执行上传图片"""
        pass


class UploadVideoUseCase(ABC):
    """上传视频的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UploadVideoRequest) -> MediaResponse:
        """执行上传视频"""
        pass


class DeleteMediaUseCase(ABC):
    """删除 Media 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteMediaRequest) -> MediaResponse:
        """执行删除 Media"""
        pass


class RestoreMediaUseCase(ABC):
    """恢复 Media 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: RestoreMediaRequest) -> MediaResponse:
        """执行恢复 Media"""
        pass


class PurgeMediaUseCase(ABC):
    """硬删除 Media 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: PurgeMediaRequest) -> None:
        """执行硬删除 Media"""
        pass


class AssociateMediaUseCase(ABC):
    """关联 Media 到 Entity 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: AssociateMediaRequest) -> None:
        """执行关联 Media"""
        pass


class DisassociateMediaUseCase(ABC):
    """移除 Media 与 Entity 关联的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DisassociateMediaRequest) -> None:
        """执行移除关联"""
        pass


class GetMediaUseCase(ABC):
    """获取 Media 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetMediaRequest) -> MediaResponse:
        """执行获取 Media"""
        pass


class UpdateMediaMetadataUseCase(ABC):
    """更新 Media 元数据的 UseCase 接口"""

    @abstractmethod
    async def execute_update_image(self, request: UpdateImageMetadataRequest) -> MediaResponse:
        """执行更新图片元数据"""
        pass

    @abstractmethod
    async def execute_update_video(self, request: UpdateVideoMetadataRequest) -> MediaResponse:
        """执行更新视频元数据"""
        pass
