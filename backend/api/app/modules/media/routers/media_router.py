"""
Media Router - Hexagonal Architecture Pattern

FastAPI 路由适配器，�?HTTP 请求转换�?UseCase 调用�?
职责:
1. 解析 HTTP 请求 �?转换�?Input DTO
2. �?DI 容器获取 UseCase
3. 执行 UseCase
4. �?Output DTO �?转换�?HTTP 响应
5. 异常映射�?HTTP 错误�?
POLICY-010: 30-day trash retention for soft delete
POLICY-009: Storage quota and MIME type validation
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from typing import Optional, List
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from modules.media.application.ports.input import (
    UploadImageRequest,
    UploadVideoRequest,
    DeleteMediaRequest,
    RestoreMediaRequest,
    PurgeMediaRequest,
    AssociateMediaRequest,
    DisassociateMediaRequest,
    GetMediaRequest,
    UpdateMediaMetadataRequest,
    MediaResponse,
)
from modules.media.domain.exceptions import (
    MediaNotFoundError,
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    StorageQuotaExceededError,
    MediaInTrashError,
    CannotPurgeError,
    AssociationError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


# ============================================================================
# Dependency: Get DI Container
# ============================================================================

async def get_di_container() -> DIContainer:
    """
    获取 DI 容器（FastAPI 依赖�?
    在实际应用中，这会从全局初始化的容器获取�?    """
    return get_di_container_provider()


# ============================================================================
# Endpoints: Image & Video Upload
# ============================================================================

@router.post(
    "/images",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
    description="""
    上传图片文件到全局媒体存储（POLICY-009: Storage Quota, MIME Type Validation�?
    支持格式: JPEG, PNG, WEBP, GIF
    """
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    description: Optional[str] = Query(None, description="Optional image description"),
    di: DIContainer = Depends(get_di_container)
):
    """
    上传图片

    POLICY-009: Enforces MIME type validation and file size limits
    """
    try:
        content = await file.read()

        request = UploadImageRequest(
            filename=file.filename,
            mime_type=file.content_type,
            file_content=content,
            description=description
        )

        use_case = di.get_upload_image_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except InvalidMimeTypeError as e:
        logger.warning(f"Invalid MIME type for image: {file.filename} ({file.content_type})")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except FileSizeTooLargeError as e:
        logger.warning(f"File size too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except StorageQuotaExceededError as e:
        logger.warning(f"Storage quota exceeded during upload")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error during image upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/videos",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video",
    description="""
    上传视频文件到全局媒体存储（POLICY-009: Storage Quota, MIME Type Validation�?
    支持格式: MP4, WEBM, OGG
    """
)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload"),
    description: Optional[str] = Query(None, description="Optional video description"),
    di: DIContainer = Depends(get_di_container)
):
    """
    上传视频

    POLICY-009: Enforces MIME type validation and file size limits
    """
    try:
        content = await file.read()

        request = UploadVideoRequest(
            filename=file.filename,
            mime_type=file.content_type,
            file_content=content,
            description=description
        )

        use_case = di.get_upload_video_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except InvalidMimeTypeError as e:
        logger.warning(f"Invalid MIME type for video: {file.filename} ({file.content_type})")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except FileSizeTooLargeError as e:
        logger.warning(f"File size too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except StorageQuotaExceededError as e:
        logger.warning(f"Storage quota exceeded during upload")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error during video upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Endpoints: Media Retrieval & Update
# ============================================================================

@router.get(
    "/{media_id}",
    response_model=dict,
    summary="Get media by ID",
    description="获取媒体文件的详情（包括元数据）"
)
async def get_media(
    media_id: UUID = Query(..., description="Media ID"),
    di: DIContainer = Depends(get_di_container)
):
    """获取媒体详情"""
    try:
        request = GetMediaRequest(media_id=media_id)
        use_case = di.get_get_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        logger.info(f"Media not found: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error retrieving media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/{media_id}",
    response_model=dict,
    summary="Update media metadata",
    description="更新媒体元数据（图像尺寸、视频时长等�?
)
async def update_media_metadata(
    media_id: UUID = Query(..., description="Media ID"),
    description: Optional[str] = Query(None, description="Updated description"),
    width: Optional[int] = Query(None, ge=1, description="Image width for image media"),
    height: Optional[int] = Query(None, ge=1, description="Image height for image media"),
    duration_ms: Optional[int] = Query(None, ge=1, description="Video duration in milliseconds for video media"),
    di: DIContainer = Depends(get_di_container)
):
    """更新媒体元数�?""
    try:
        request = UpdateMediaMetadataRequest(
            media_id=media_id,
            description=description,
            width=width,
            height=height,
            duration_ms=duration_ms
        )

        use_case = di.get_update_media_metadata_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        logger.info(f"Media not found for update: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error updating media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Endpoints: Media Deletion (Soft Delete & Purge) - POLICY-010
# ============================================================================

@router.delete(
    "/{media_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete media (move to trash)",
    description="""
    软删除：将媒体移到垃圾箱

    POLICY-010: 30-day trash retention before hard deletion
    可通过 /restore 在保留期内恢�?    """
)
async def delete_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """
    删除媒体（移到垃圾箱�?
    POLICY-010: Media remains in trash for 30 days before purge eligibility
    """
    try:
        request = DeleteMediaRequest(media_id=media_id)
        use_case = di.get_delete_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        logger.info(f"Media moved to trash: {media_id}")
        return response.to_dict()
    except MediaNotFoundError as e:
        logger.info(f"Media not found for deletion: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error deleting media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{media_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore media from trash",
    description="""
    恢复媒体：将媒体从垃圾箱恢复到活跃状�?
    POLICY-010: 可在30天保留期内恢�?    """
)
async def restore_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """
    恢复媒体（从垃圾箱恢复）

    POLICY-010: Can only restore within 30-day retention period
    """
    try:
        request = RestoreMediaRequest(media_id=media_id)
        use_case = di.get_restore_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        logger.info(f"Media restored from trash: {media_id}")
        return response.to_dict()
    except MediaNotFoundError as e:
        logger.info(f"Media not found for restore: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except MediaInTrashError as e:
        logger.warning(f"Cannot restore media not in trash: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error restoring media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{media_id}/purge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete media",
    description="""
    硬删除：永久删除媒体文件

    POLICY-010: 仅允许在垃圾箱中30天后执行
    """
)
async def purge_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """
    彻底删除媒体（永久删除）

    POLICY-010: Only allowed for media in trash >= 30 days
    """
    try:
        request = PurgeMediaRequest(media_id=media_id)
        use_case = di.get_purge_media_use_case()
        await use_case.execute(request)
        logger.info(f"Media permanently purged: {media_id}")
    except MediaNotFoundError as e:
        logger.info(f"Media not found for purge: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CannotPurgeError as e:
        logger.warning(f"Cannot purge media (not yet eligible): {media_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error purging media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Endpoints: Media Association (Link to Entities)
# ============================================================================

@router.post(
    "/{media_id}/associate",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Associate media with entity",
    description="""
    关联媒体到实体（Book/Bookshelf/Block�?
    一个媒体可以关联到多个实体，但不能重复关联到同一个实�?    """
)
async def associate_media(
    media_id: UUID,
    entity_type: str = Query(
        ...,
        description="Entity type: BOOKSHELF | BOOK | BLOCK",
        regex="^(BOOKSHELF|BOOK|BLOCK)$"
    ),
    entity_id: UUID = Query(..., description="Target entity ID"),
    di: DIContainer = Depends(get_di_container)
):
    """
    关联媒体到实体（Book/Bookshelf/Block�?
    一个媒体可以关联到多个不同的实�?    """
    try:
        request = AssociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_associate_media_use_case()
        await use_case.execute(request)
        logger.info(f"Media {media_id} associated with {entity_type} {entity_id}")
        return {"message": "Media associated successfully", "media_id": str(media_id)}
    except MediaNotFoundError as e:
        logger.info(f"Media not found for association: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AssociationError as e:
        logger.warning(f"Association error for media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error associating media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{media_id}/disassociate",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Disassociate media from entity",
    description="""
    取消关联：断开媒体与实体的关联

    媒体文件不会被删除，只是移除了关联关�?    """
)
async def disassociate_media(
    media_id: UUID,
    entity_type: str = Query(
        ...,
        description="Entity type: BOOKSHELF | BOOK | BLOCK",
        regex="^(BOOKSHELF|BOOK|BLOCK)$"
    ),
    entity_id: UUID = Query(..., description="Target entity ID"),
    di: DIContainer = Depends(get_di_container)
):
    """
    取消关联媒体

    媒体文件本身不会被删除，只是移除关联
    """
    try:
        request = DisassociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_disassociate_media_use_case()
        await use_case.execute(request)
        logger.info(f"Media {media_id} disassociated from {entity_type} {entity_id}")
        return {"message": "Media disassociated successfully", "media_id": str(media_id)}
    except MediaNotFoundError as e:
        logger.info(f"Media not found for disassociation: {media_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AssociationError as e:
        logger.warning(f"Disassociation error for media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error disassociating media {media_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]

