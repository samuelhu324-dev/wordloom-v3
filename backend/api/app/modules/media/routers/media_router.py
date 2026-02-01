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
import time
import uuid
from pathlib import Path as FilePath
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, File, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.media.schemas import MediaResponse as MediaDetailResponse
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
from api.app.modules.media.exceptions import (
    MediaNotFoundError as MediaNotFoundErrorV2,
    DomainException as DomainExceptionV2,
)
from api.app.shared.request_context import RequestContext
from infra.database import get_db_session
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository
from infra.storage.storage_manager import LocalStorageStrategy, StorageManager

from api.app.modules.media.routers import mappers as media_mappers
from api.app.modules.media.routers.schemas import (
    UploadImageQuery,
    UploadVideoQuery,
    UpdateMediaMetadataBody,
    AssociateMediaQuery,
    DisassociateMediaQuery,
    PurgeMediaQuery,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["media"])

_BACKEND_ROOT = FilePath(__file__).resolve().parents[5]
_STORAGE_ROOT = FilePath(os.getenv("WORDLOOM_STORAGE_ROOT", _BACKEND_ROOT / "storage")).resolve()
_media_storage = StorageManager(LocalStorageStrategy(str(_STORAGE_ROOT)))


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
    query: UploadImageQuery = Depends(),
    di: DIContainer = Depends(get_di_container)
):
    """Upload an image file to media storage"""
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is empty",
            )

        filename = (file.filename or "image").replace(" ", "_")
        storage_key = await _media_storage.save_media_file(content, filename)
        try:
            command = media_mappers.to_upload_image_command(
                filename=filename,
                content_type=file.content_type,
                file_size=len(content),
                storage_key=storage_key,
            )
            use_case = di.get_upload_image_use_case()
            media = await use_case.execute_command(command)
            return MediaDetailResponse.model_validate(media)
        except Exception:
            await _media_storage.delete_file(storage_key)
            raise
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
    query: UploadVideoQuery = Depends(),
    di: DIContainer = Depends(get_di_container)
):
    """Upload a video file to media storage"""
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video file is empty",
            )

        filename = (file.filename or "video").replace(" ", "_")
        storage_key = await _media_storage.save_media_file(content, filename)
        try:
            command = media_mappers.to_upload_video_command(
                filename=filename,
                content_type=file.content_type,
                file_size=len(content),
                storage_key=storage_key,
            )
            use_case = di.get_upload_video_use_case()
            media = await use_case.execute_command(command)
            return MediaDetailResponse.model_validate(media)
        except Exception:
            await _media_storage.delete_file(storage_key)
            raise
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
    request: Request,
    media_id: UUID = Path(..., description="Media ID"),
    di: DIContainer = Depends(get_di_container)
):
    """Get detailed information about a media file"""
    start = time.perf_counter()
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Request-Id") or str(uuid.uuid4())
    ctx = RequestContext(
        correlation_id=correlation_id,
        actor_id=None,
        workspace_id=None,
        route=str(request.url.path),
        method=request.method,
    )

    logger.info(
        {
            "event": "media.get.request_received",
            "operation": "media.get",
            "layer": "handler",
            "correlation_id": ctx.correlation_id,
            "media_id": str(media_id),
            "route": ctx.route,
            "method": ctx.method,
        }
    )

    try:
        use_case = di.get_media_use_case()
        media = await use_case.execute(media_id, ctx=ctx)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            {
                "event": "media.get.success",
                "operation": "media.get",
                "layer": "handler",
                "outcome": "success",
                "correlation_id": ctx.correlation_id,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
            }
        )

        return MediaDetailResponse.model_validate(media)
    except (MediaNotFoundError, MediaNotFoundErrorV2):
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            {
                "event": "media.get.not_found",
                "operation": "media.get",
                "layer": "handler",
                "outcome": "not_found",
                "correlation_id": ctx.correlation_id,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
                "error_type": "MediaNotFoundError",
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    except (DomainException, DomainExceptionV2) as e:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error(
            {
                "event": "media.get.failed",
                "operation": "media.get",
                "layer": "handler",
                "outcome": "error",
                "correlation_id": ctx.correlation_id,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            {
                "event": "media.get.failed",
                "operation": "media.get",
                "layer": "handler",
                "outcome": "error",
                "correlation_id": ctx.correlation_id,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )
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
    request: Request,
    media_id: UUID = Path(..., description="Media ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """Return the raw media binary referenced by the media record."""
    start = time.perf_counter()
    req_method = request.method
    req_path = str(request.url.path)
    query_cid = request.query_params.get("cid")
    correlation_id = (
        query_cid
        or getattr(request.state, "correlation_id", None)
        or request.headers.get("X-Request-Id")
        or str(uuid.uuid4())
    )
    # Ensure middleware (and downstream code) sees the same correlation id.
    request.state.correlation_id = correlation_id

    ctx = RequestContext(
        correlation_id=correlation_id,
        actor_id=None,
        workspace_id=None,
        route=str(request.url.path),
        method=request.method,
    )

    logger.info(
        {
            "event": "media.file.request_received",
            "operation": "media.file",
            "layer": "handler",
            "correlation_id": ctx.correlation_id,
            "cid": query_cid,
            "cache_bust": request.query_params.get("v"),
            "media_id": str(media_id),
            "route": ctx.route,
            "method": req_method,
            "path": req_path,
        }
    )

    repository = SQLAlchemyMediaRepository(session)
    try:
        db_start = time.perf_counter()
        media = await repository.get_by_id(media_id, ctx=ctx)
        db_duration_ms = (time.perf_counter() - db_start) * 1000
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            {
                "event": "media.file.failed",
                "operation": "media.file",
                "layer": "handler",
                "outcome": "error",
                "correlation_id": ctx.correlation_id,
                "cid": query_cid,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "method": req_method,
                "path": req_path,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load media metadata",
        ) from exc

    if not media:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            {
                "event": "media.file.not_found",
                "operation": "media.file",
                "layer": "handler",
                "outcome": "not_found",
                "correlation_id": ctx.correlation_id,
                "cid": query_cid,
                "media_id": str(media_id),
                "duration_ms": duration_ms,
                "method": req_method,
                "path": req_path,
                "status_code": status.HTTP_404_NOT_FOUND,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found",
        )

    logger.info(
        {
            "event": "media.file.db_loaded",
            "operation": "media.file",
            "layer": "handler",
            "correlation_id": ctx.correlation_id,
            "cid": query_cid,
            "media_id": str(media_id),
            "storage_key": getattr(media, "storage_key", None),
            "db_duration_ms": db_duration_ms,
            "method": req_method,
            "path": req_path,
        }
    )

    resolve_start = time.perf_counter()
    file_path = _resolve_storage_path(media.storage_key)
    resolve_duration_ms = (time.perf_counter() - resolve_start) * 1000

    logger.info(
        {
            "event": "media.file.storage_resolved",
            "operation": "media.file",
            "layer": "handler",
            "correlation_id": ctx.correlation_id,
            "cid": query_cid,
            "media_id": str(media_id),
            "storage_key": getattr(media, "storage_key", None),
            "file_path": str(file_path),
            # Keep both names for compatibility; storage_duration_ms is the recommended field.
            "storage_duration_ms": resolve_duration_ms,
            "resolve_duration_ms": resolve_duration_ms,
            "method": req_method,
            "path": req_path,
        }
    )

    if not file_path.is_file():
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error(
            {
                "event": "media.file.file_missing",
                "operation": "media.file",
                "layer": "handler",
                "outcome": "file_missing",
                "correlation_id": ctx.correlation_id,
                "cid": query_cid,
                "media_id": str(media_id),
                "storage_key": getattr(media, "storage_key", None),
                "file_path": str(file_path),
                "storage_duration_ms": resolve_duration_ms,
                "resolve_duration_ms": resolve_duration_ms,
                "duration_ms": duration_ms,
                "method": req_method,
                "path": req_path,
                "status_code": status.HTTP_404_NOT_FOUND,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    try:
        file_size_bytes = file_path.stat().st_size
    except OSError as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            {
                "event": "media.file.failed",
                "operation": "media.file",
                "layer": "handler",
                "outcome": "error",
                "correlation_id": ctx.correlation_id,
                "cid": query_cid,
                "media_id": str(media_id),
                "file_path": str(file_path),
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "method": req_method,
                "path": req_path,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read media file",
        ) from exc

    media_type = getattr(media.mime_type, "value", str(media.mime_type))

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        {
            "event": "media.file.response_prepared",
            "operation": "media.file",
            "layer": "handler",
            "outcome": "success",
            "correlation_id": ctx.correlation_id,
            "cid": query_cid,
            "cache_bust": request.query_params.get("v"),
            "media_id": str(media_id),
            "filename": getattr(media, "filename", None),
            "mime_type": media_type,
            "storage_key": getattr(media, "storage_key", None),
            "file_path": str(file_path),
            "file_size_bytes": file_size_bytes,
            "db_duration_ms": db_duration_ms,
            "storage_duration_ms": resolve_duration_ms,
            "resolve_duration_ms": resolve_duration_ms,
            "duration_ms": duration_ms,
            "method": req_method,
            "path": req_path,
            "status_code": status.HTTP_200_OK,
        }
    )

    def _log_response_sent() -> None:
        total_duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            {
                "event": "media.file.response_sent",
                "operation": "media.file",
                "layer": "handler",
                "outcome": "success",
                "correlation_id": ctx.correlation_id,
                "cid": query_cid,
                "cache_bust": request.query_params.get("v"),
                "media_id": str(media_id),
                "filename": getattr(media, "filename", None),
                "mime_type": media_type,
                "storage_key": getattr(media, "storage_key", None),
                "file_path": str(file_path),
                "file_size_bytes": file_size_bytes,
                "total_duration_ms": total_duration_ms,
                "method": req_method,
                "path": req_path,
                "status_code": status.HTTP_200_OK,
            }
        )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=media.filename,
        headers={"X-Request-Id": ctx.correlation_id},
        background=BackgroundTask(_log_response_sent),
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
    body: UpdateMediaMetadataBody = None,
    di: DIContainer = Depends(get_di_container)
):
    """Update media metadata"""
    try:
        if body is None:
            body = UpdateMediaMetadataBody()

        command = media_mappers.to_update_media_metadata_command(
            media_id=media_id,
            width=body.width,
            height=body.height,
            duration_ms=body.duration_ms,
        )
        use_case = di.get_update_media_metadata_use_case()
        media = await use_case.execute_command(command)
        return MediaDetailResponse.model_validate(media)
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
    query: AssociateMediaQuery = Depends(),
    di: DIContainer = Depends(get_di_container)
):
    """Associate media with an entity"""
    try:
        use_case = di.get_associate_media_use_case()
        command = media_mappers.to_associate_media_command(
            media_id=media_id,
            entity_type=query.entity_type,
            entity_id=query.entity_id,
        )
        await use_case.execute_command(command)
        return {"ok": True}
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
    query: DisassociateMediaQuery = Depends(),
    di: DIContainer = Depends(get_di_container)
):
    """Disassociate media from an entity"""
    try:
        use_case = di.get_disassociate_media_use_case()
        command = media_mappers.to_disassociate_media_command(
            media_id=media_id,
            entity_type=query.entity_type,
            entity_id=query.entity_id,
        )
        await use_case.execute_command(command)
        return {"ok": True}
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
        use_case = di.get_delete_media_use_case()
        deleted = await use_case.execute(media_id)
        return MediaDetailResponse.model_validate(deleted)
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
        use_case = di.get_restore_media_use_case()
        restored = await use_case.execute(media_id)
        return MediaDetailResponse.model_validate(restored)
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
    query: PurgeMediaQuery = Depends(),
    di: DIContainer = Depends(get_di_container)
):
    """Permanently delete media"""
    try:
        use_case = di.get_purge_media_use_case()
        command = media_mappers.to_purge_media_command(media_id=media_id, force=query.force)
        await use_case.execute_command(command)
        return {"ok": True}
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


