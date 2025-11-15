"""
Media Input Port - Request DTOs and UseCase Interfaces

This module defines the input ports (interfaces) that application layer
use cases expose to the outside world (HTTP adapters, CLI, etc).

Request DTOs:
- UploadMediaRequest: Upload new media file
- UpdateMediaMetadataRequest: Update media metadata
- AssociateMediaRequest: Associate media with entity
- DisassociateMediaRequest: Remove media-entity association
- RestoreMediaRequest: Restore media from trash
- BatchRestoreRequest: Batch restore multiple media
- PurgeExpiredMediaRequest: Hard delete expired media

Response DTOs:
- UploadMediaResponse: Response after upload
- MediaResponse: Single media details
- MediaListResponse: List of media
- MediaTrashResponse: Trash media details
- EntityMediaListResponse: Media associated with entity

UseCase Interfaces:
- IUploadMediaUseCase: Upload media file
- IUpdateMediaMetadataUseCase: Update metadata
- IGetMediaUseCase: Retrieve media
- IListMediaUseCase: List media
- IAssociateMediaUseCase: Associate with entity
- IDisassociateMediaUseCase: Remove association
- IMoveMediaToTrashUseCase: Soft delete
- IRestoreMediaUseCase: Restore from trash
- IPurgeExpiredMediaUseCase: Hard delete
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UploadMediaRequest(BaseModel):
    """Base class: Request to upload new media file"""
    filename: str
    mime_type: str
    file_size: int


class UploadImageRequest(BaseModel):
    """Request to upload image file"""
    filename: str
    mime_type: str
    file_content: bytes
    description: Optional[str] = None


class UploadVideoRequest(BaseModel):
    """Request to upload video file"""
    filename: str
    mime_type: str
    file_content: bytes
    description: Optional[str] = None


class DeleteMediaRequest(BaseModel):
    """Request to delete media"""
    media_id: UUID


class GetMediaRequest(BaseModel):
    """Request to get media"""
    media_id: UUID


class PurgeMediaRequest(BaseModel):
    """Request to purge media"""
    media_id: UUID


class UploadMediaResponse(BaseModel):
    """Response after successful upload"""
    id: str
    filename: str
    storage_key: str
    created_at: datetime


class UpdateMediaMetadataRequest(BaseModel):
    """Request to update media metadata"""
    media_id: UUID
    filename: Optional[str] = None
    description: Optional[str] = None


class MediaResponse(BaseModel):
    """Single media item response"""
    id: str
    filename: str
    mime_type: str
    state: str
    created_at: datetime
    updated_at: datetime


class MediaListResponse(BaseModel):
    """List of media items"""
    items: List[MediaResponse]
    total: int


class MediaTrashResponse(BaseModel):
    """Media in trash"""
    id: str
    filename: str
    trashed_at: datetime
    expires_at: datetime


class AssociateMediaRequest(BaseModel):
    """Request to associate media with entity"""
    media_id: UUID
    entity_type: str
    entity_id: UUID


class DisassociateMediaRequest(BaseModel):
    """Request to remove media-entity association"""
    media_id: UUID
    entity_type: str
    entity_id: UUID


class RestoreMediaRequest(BaseModel):
    """Request to restore media from trash"""
    media_id: UUID


class BatchRestoreRequest(BaseModel):
    """Request to batch restore media"""
    media_ids: List[UUID]


class PurgeExpiredMediaRequest(BaseModel):
    """Request to purge expired media"""
    older_than_days: int = 30


class EntityMediaListResponse(BaseModel):
    """Media associated with entity"""
    entity_type: str
    entity_id: str
    media_list: List[MediaResponse]


# UseCase Interfaces

class IUploadMediaUseCase(ABC):
    """UseCase: Upload new media file"""

    @abstractmethod
    async def execute(self, request: UploadMediaRequest) -> UploadMediaResponse:
        """Upload media and return response"""
        pass


class IUpdateMediaMetadataUseCase(ABC):
    """UseCase: Update media metadata"""

    @abstractmethod
    async def execute(self, request: UpdateMediaMetadataRequest) -> MediaResponse:
        """Update metadata and return media"""
        pass


class IGetMediaUseCase(ABC):
    """UseCase: Get single media by ID"""

    @abstractmethod
    async def execute(self, media_id: UUID) -> MediaResponse:
        """Get media by ID"""
        pass


class IListMediaUseCase(ABC):
    """UseCase: List all active media"""

    @abstractmethod
    async def execute(self, skip: int = 0, limit: int = 100) -> MediaListResponse:
        """List media with pagination"""
        pass


class IAssociateMediaUseCase(ABC):
    """UseCase: Associate media with entity"""

    @abstractmethod
    async def execute(self, request: AssociateMediaRequest) -> None:
        """Associate media with entity"""
        pass


class IDisassociateMediaUseCase(ABC):
    """UseCase: Remove media-entity association"""

    @abstractmethod
    async def execute(self, request: DisassociateMediaRequest) -> None:
        """Remove association"""
        pass


class IMoveMediaToTrashUseCase(ABC):
    """UseCase: Move media to trash (soft delete)"""

    @abstractmethod
    async def execute(self, media_id: UUID) -> None:
        """Move media to trash"""
        pass


class IRestoreMediaUseCase(ABC):
    """UseCase: Restore media from trash"""

    @abstractmethod
    async def execute(self, request: RestoreMediaRequest) -> MediaResponse:
        """Restore media from trash"""
        pass


class IPurgeExpiredMediaUseCase(ABC):
    """UseCase: Hard delete expired media"""

    @abstractmethod
    async def execute(self, request: PurgeExpiredMediaRequest) -> int:
        """Purge expired media, return count deleted"""
        pass
