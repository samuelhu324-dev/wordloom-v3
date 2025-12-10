"""
Media Router - Hexagonal Architecture Pattern

FastAPI router adapter that:
1. Parses HTTP requests and converts to Input DTOs
2. Gets UseCases from DI container
3. Executes UseCases
4. Converts Output DTOs to HTTP responses
5. Maps domain exceptions to HTTP errors

Policies:
- POLICY-010: 30-day trash retention for soft delete
- POLICY-009: Storage quota and MIME type validation
"""

import logging
import os
from dataclasses import asdict
from pathlib import Path as FilePath
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.media.application.ports.input import (
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
from api.app.modules.media.domain.exceptions import (
    MediaNotFoundError,
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    StorageQuotaExceededError,
    MediaInTrashError,
    CannotPurgeError,
    AssociationError,
    DomainException,
)
from infra.database import get_db_session
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository


logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["media"])

_BACKEND_ROOT = FilePath(__file__).resolve().parents[5]
_STORAGE_ROOT = FilePath(os.getenv("WORDLOOM_STORAGE_ROOT", _BACKEND_ROOT / "storage")).resolve()


def _resolve_storage_path(storage_key: str) -> FilePath:
    """Resolve storage key into an absolute path under the storage root."""
    candidate = (_STORAGE_ROOT / storage_key).resolve()
    try:
        candidate.relative_to(_STORAGE_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid media storage key",
        )
    return candidate


# ============================================================================
# Endpoints: Image Upload
# ============================================================================

@router.post(
    "/images",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image",
    description="Upload image file to global media storage (JPEG, PNG, WEBP, GIF)"
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    description: Optional[str] = Query(None, description="Optional image description"),
    di: DIContainer = Depends(get_di_container)
):
    """Upload an image file to media storage"""
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
        return asdict(response)
    except InvalidMimeTypeError as e:
        logger.warning(f"Invalid MIME type for image: {file.filename} ({file.content_type})")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image MIME type: {file.content_type}"
        )
    except FileSizeTooLargeError as e:
        logger.warning(f"File size too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image file is too large"
        )
    except StorageQuotaExceededError as e:
        logger.warning(f"Storage quota exceeded for image: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Storage quota exceeded"
        )
    except DomainException as e:
        logger.error(f"Domain error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


# ============================================================================
# Endpoints: Video Upload
# ============================================================================

@router.post(
    "/videos",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video",
    description="Upload video file to global media storage (MP4, WebM, etc.)"
)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload"),
    description: Optional[str] = Query(None, description="Optional video description"),
    di: DIContainer = Depends(get_di_container)
):
    """Upload a video file to media storage"""
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
        return asdict(response)
    except InvalidMimeTypeError as e:
        logger.warning(f"Invalid MIME type for video: {file.filename} ({file.content_type})")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid video MIME type: {file.content_type}"
        )
    except FileSizeTooLargeError as e:
        logger.warning(f"File size too large: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Video file is too large"
        )
    except StorageQuotaExceededError as e:
        logger.warning(f"Storage quota exceeded for video: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Storage quota exceeded"
        )
    except DomainException as e:
        logger.error(f"Domain error uploading video: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video"
        )


# ============================================================================
# Endpoints: Get Media
# ============================================================================

@router.get(
    "/{media_id}",
    response_model=None,
    summary="Get media details",
    description="Retrieve detailed information about a specific media file"
)
async def get_media(
    media_id: UUID = Path(..., description="Media ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Get detailed information about a media file"""
    try:
        request = GetMediaRequest(media_id=media_id)
        use_case = di.get_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except DomainException as e:
        logger.error(f"Domain error getting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get media"
        )


# ============================================================================
# Endpoints: Download Media File
# ============================================================================

@router.get(
    "/{media_id}/file",
    response_class=FileResponse,
    summary="Download media file",
    description="Stream the stored media file from disk"
)
async def download_media_file(
    media_id: UUID = Path(..., description="Media ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """Return the raw media binary referenced by the media record."""
    repository = SQLAlchemyMediaRepository(session)
    try:
        media = await repository.get_by_id(media_id)
    except Exception as exc:
        logger.exception("Failed to load media %s", media_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load media metadata",
        ) from exc

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found",
        )

    file_path = _resolve_storage_path(media.storage_key)
    if not file_path.is_file():
        logger.error("Media file missing on disk for %s (expected %s)", media_id, file_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    media_type = getattr(media.mime_type, "value", str(media.mime_type))
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=media.filename,
    )


# ============================================================================
# Endpoints: Update Media Metadata
# ============================================================================

@router.patch(
    "/{media_id}",
    response_model=None,
    summary="Update media metadata",
    description="Update media metadata (description, custom fields, etc.)"
)
async def update_media_metadata(
    media_id: UUID = Path(..., description="Media ID"),
    description: Optional[str] = Query(None, description="Updated description"),
    di: DIContainer = Depends(get_di_container)
):
    """Update media metadata"""
    try:
        request = UpdateMediaMetadataRequest(
            media_id=media_id,
            description=description
        )
        use_case = di.get_update_media_metadata_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except MediaInTrashError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Media {media_id} is in trash"
        )
    except DomainException as e:
        logger.error(f"Domain error updating media metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error updating media metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update media metadata"
        )


# ============================================================================
# Endpoints: Associate Media with Entity
# ============================================================================

@router.post(
    "/associate",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Associate media with entity",
    description="Associate a media file with a book, block, or other entity"
)
async def associate_media(
    media_id: UUID = Path(..., description="Media ID"),
    entity_type: str = Query(..., description="Entity type (book, block, etc.)"),
    entity_id: UUID = Query(..., description="Entity ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Associate media with an entity"""
    try:
        request = AssociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_associate_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except AssociationError as e:
        logger.warning(f"Association error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error associating media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error associating media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate media"
        )


# ============================================================================
# Endpoints: Disassociate Media from Entity
# ============================================================================

@router.post(
    "/disassociate",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Disassociate media from entity",
    description="Remove association between media and an entity"
)
async def disassociate_media(
    media_id: UUID = Path(..., description="Media ID"),
    entity_type: str = Query(..., description="Entity type (book, block, etc.)"),
    entity_id: UUID = Query(..., description="Entity ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Disassociate media from an entity"""
    try:
        request = DisassociateMediaRequest(
            media_id=media_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        use_case = di.get_disassociate_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except AssociationError as e:
        logger.warning(f"Disassociation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error disassociating media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error disassociating media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disassociate media"
        )


# ============================================================================
# Endpoints: Delete Media (Soft Delete)
# ============================================================================

@router.delete(
    "/{media_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Move media to trash",
    description="Soft delete media (moved to trash, retained for 30 days per POLICY-010)"
)
async def delete_media(
    media_id: UUID = Path(..., description="Media ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Move media to trash (soft delete)"""
    try:
        request = DeleteMediaRequest(media_id=media_id)
        use_case = di.get_delete_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except DomainException as e:
        logger.error(f"Domain error deleting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media"
        )


# ============================================================================
# Endpoints: Restore Media from Trash
# ============================================================================

@router.post(
    "/{media_id}/restore",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Restore media from trash",
    description="Restore media that was previously moved to trash"
)
async def restore_media(
    media_id: UUID = Path(..., description="Media ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Restore media from trash"""
    try:
        request = RestoreMediaRequest(media_id=media_id)
        use_case = di.get_restore_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except DomainException as e:
        logger.error(f"Domain error restoring media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error restoring media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore media"
        )


# ============================================================================
# Endpoints: Purge Media (Hard Delete)
# ============================================================================

@router.delete(
    "/{media_id}/purge",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Permanently delete media",
    description="Permanently remove media file and its database record (cannot be undone)"
)
async def purge_media(
    media_id: UUID = Path(..., description="Media ID"),
    force: bool = Query(False, description="Force purge even if not in trash"),
    di: DIContainer = Depends(get_di_container)
):
    """Permanently delete media"""
    try:
        request = PurgeMediaRequest(media_id=media_id, force=force)
        use_case = di.get_purge_media_use_case()
        response: MediaResponse = await use_case.execute(request)
        return asdict(response)
    except MediaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except CannotPurgeError as e:
        logger.warning(f"Cannot purge media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainException as e:
        logger.error(f"Domain error purging media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error purging media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to purge media"
        )


