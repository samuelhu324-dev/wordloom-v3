"""
Media Router - Hexagonal Architecture Pattern

FastAPI 路由适配器，处理媒体上传、管理和关联。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from typing import Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.media.application.ports.input import (
    UploadImageRequest,
    UploadVideoRequest,
    DeleteMediaRequest,
    RestoreMediaRequest,
    PurgeMediaRequest,
    AssociateMediaRequest,
    DisassociateMediaRequest,
    GetMediaRequest,
    MediaResponse,
)
from app.modules.media.domain.exceptions import (
    MediaNotFoundError,
    MediaInvalidTypeError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


# ============================================================================
# Image Upload Endpoint
# ============================================================================

@router.post(
    "/images",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
)
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Query(None),
    di: DIContainer = Depends(get_di_container)
):
    """上传图片"""
    try:
        # 读取文件内容
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
    except MediaInvalidTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Video Upload Endpoint
# ============================================================================

@router.post(
    "/videos",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video",
)
async def upload_video(
    file: UploadFile = File(...),
    description: Optional[str] = Query(None),
    di: DIContainer = Depends(get_di_container)
):
    """上传视频"""
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
    except MediaInvalidTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Media Retrieval Endpoints
# ============================================================================

@router.get(
    "/{media_id}",
    response_model=dict,
    summary="Get media by ID",
)
async def get_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取媒体详情"""
    try:
        request = GetMediaRequest(media_id=media_id)
        use_case = di.get_get_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Media Update Endpoint
# ============================================================================

@router.patch(
    "/{media_id}",
    response_model=dict,
    summary="Update media metadata",
)
async def update_media_metadata(
    media_id: UUID,
    description: Optional[str] = Query(None),
    media_type: Optional[str] = Query(None),
    di: DIContainer = Depends(get_di_container)
):
    """更新媒体元数据"""
    try:
        from app.modules.media.application.ports.input import UpdateImageMetadataRequest

        request = UpdateImageMetadataRequest(
            media_id=media_id,
            description=description
        )

        use_case = di.get_update_media_metadata_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Media Deletion Endpoints
# ============================================================================

@router.delete(
    "/{media_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete media (move to trash)",
)
async def delete_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除媒体（移到垃圾箱）"""
    try:
        request = DeleteMediaRequest(media_id=media_id)
        use_case = di.get_delete_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{media_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore media from trash",
)
async def restore_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """恢复媒体（从垃圾箱恢复）"""
    try:
        request = RestoreMediaRequest(media_id=media_id)
        use_case = di.get_restore_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return response.to_dict()
    except MediaNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{media_id}/purge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete media",
)
async def purge_media(
    media_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """彻底删除媒体（永久删除）"""
    try:
        request = PurgeMediaRequest(media_id=media_id)
        use_case = di.get_purge_media_use_case()
        await use_case.execute(request)
    except MediaNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Media Association Endpoints
# ============================================================================

@router.post(
    "/{media_id}/associate",
    status_code=status.HTTP_200_OK,
    summary="Associate media with entity",
)
async def associate_media(
    media_id: UUID,
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    di: DIContainer = Depends(get_di_container)
):
    """关联媒体到实体"""
    try:
        request = AssociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_associate_media_use_case()
        await use_case.execute(request)
        return {"message": "Media associated successfully"}
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{media_id}/disassociate",
    status_code=status.HTTP_200_OK,
    summary="Disassociate media from entity",
)
async def disassociate_media(
    media_id: UUID,
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    di: DIContainer = Depends(get_di_container)
):
    """取消关联媒体"""
    try:
        request = DisassociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_disassociate_media_use_case()
        await use_case.execute(request)
        return {"message": "Media disassociated successfully"}
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
