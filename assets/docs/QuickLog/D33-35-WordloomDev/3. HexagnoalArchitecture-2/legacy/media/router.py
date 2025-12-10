"""Media Router - FastAPI endpoints for media management

Architecture (ADR-026: Media Router & API):
===========================================
- Dependency injection: FastAPI → router → service → repository → domain
- Exception handling with HTTP status code mapping
- Request/response validation with Pydantic schemas
- Structured logging for debugging
- Multipart file upload handling

Endpoints:
- POST /media/upload - Upload media file
- DELETE /media/{id} - Soft delete media (move to trash)
- POST /media/{id}/restore - Restore from trash
- POST /media/restore-batch - Restore multiple media
- GET /media/trash - List trash media (paginated)
- POST /media/purge-expired - Auto-purge 30+ day trash
- GET /media/{entity_type}/{entity_id} - Get media for entity
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional
from uuid import UUID
import logging

from schemas import (
    UploadMediaRequest, UploadMediaResponse, MediaResponse,
    MediaListResponse, MediaTrashListResponse, MediaTrashResponse,
    RestoreMediaRequest, BatchRestoreRequest, BatchRestoreResponse,
    PurgeExpiredMediaRequest, PurgeExpiredResponse,
    EntityMediaListResponse, ErrorResponse,
    AssociateMediaRequest, DisassociateMediaRequest,
    EntityTypeSchema
)
from service import MediaService
from repository import MediaRepository, SQLAlchemyMediaRepository
from exceptions import (
    DomainException, MediaException,
    MediaNotFoundError, InvalidMimeTypeError,
    FileSizeTooLargeError, StorageQuotaExceededError,
    MediaInTrashError, CannotRestoreError, CannotPurgeError,
    MediaOperationError,
)
from domain import EntityTypeForMedia


logger = logging.getLogger(__name__)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/media", tags=["media"])


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_media_service(
    db_session = Depends(...)  # Database session from FastAPI Depends
) -> MediaService:
    """Dependency: Get MediaService with repository"""
    repository = SQLAlchemyMediaRepository(db_session)
    return MediaService(repository)


# ============================================================================
# Request Handlers
# ============================================================================

@router.post(
    "/upload",
    response_model=UploadMediaResponse,
    status_code=201,
    summary="Upload media file",
    responses={
        201: {"description": "Media uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Invalid media type"},
        429: {"model": ErrorResponse, "description": "Storage quota exceeded"},
    }
)
async def upload_media(
    file: UploadFile = File(...),
    force_media_type: Optional[str] = None,
    storage_quota: int = 1024 * 1024 * 1024,
    used_storage: int = 0,
    service: MediaService = Depends(get_media_service)
):
    """
    Upload a media file (image or video).

    **Supported Image Types:**
    - JPEG (image/jpeg)
    - PNG (image/png)
    - WebP (image/webp)
    - GIF (image/gif)
    - Max size: 10MB

    **Supported Video Types:**
    - MP4 (video/mp4)
    - WebM (video/webm)
    - Ogg (video/ogg)
    - Max size: 100MB

    **Process:**
    1. File is uploaded to storage backend
    2. Storage key generated for retrieval
    3. Metadata extracted (dimensions for images, duration for videos)
    4. Media record created in database
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename required")

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Determine media type from MIME
        mime_type_str = file.content_type or "application/octet-stream"

        # For now, simplified upload (in production, would write to S3/storage)
        storage_key = f"media/{file.filename}"

        # Infer media type
        if mime_type_str.startswith("image/"):
            media = await service.upload_image(
                filename=file.filename,
                mime_type=mime_type_str,
                file_size=file_size,
                storage_key=storage_key,
                storage_quota=storage_quota,
                used_storage=used_storage
            )
        elif mime_type_str.startswith("video/"):
            media = await service.upload_video(
                filename=file.filename,
                mime_type=mime_type_str,
                file_size=file_size,
                storage_key=storage_key,
                storage_quota=storage_quota,
                used_storage=used_storage
            )
        else:
            raise InvalidMimeTypeError(mime_type_str)

        logger.info(f"Media uploaded: {media.id} ({file.filename})")

        return UploadMediaResponse(
            media=MediaResponse.model_validate(media),
            message="Media uploaded successfully"
        )

    except DomainException as e:
        logger.warning(f"Upload validation error: {e.code}")
        raise HTTPException(
            status_code=e.http_status,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.delete(
    "/{media_id}",
    status_code=204,
    summary="Delete media (move to trash)",
    responses={
        204: {"description": "Media moved to trash"},
        404: {"model": ErrorResponse, "description": "Media not found"},
        409: {"model": ErrorResponse, "description": "Already in trash"},
    }
)
async def delete_media(
    media_id: UUID,
    service: MediaService = Depends(get_media_service)
):
    """Move media to trash (soft delete with 30-day retention)"""
    try:
        await service.delete_media(media_id)
        logger.info(f"Media moved to trash: {media_id}")
    except MediaException as e:
        logger.warning(f"Delete error: {e.code}")
        raise HTTPException(
            status_code=e.http_status,
            detail=e.to_dict()
        )


@router.post(
    "/{media_id}/restore",
    response_model=MediaResponse,
    summary="Restore media from trash",
    responses={
        200: {"description": "Media restored"},
        404: {"model": ErrorResponse, "description": "Media not found"},
        409: {"model": ErrorResponse, "description": "Not in trash"},
    }
)
async def restore_media(
    media_id: UUID,
    service: MediaService = Depends(get_media_service)
):
    """Restore media from trash to active state"""
    try:
        media = await service.restore_media(media_id)
        logger.info(f"Media restored: {media_id}")
        return MediaResponse.model_validate(media)
    except MediaException as e:
        logger.warning(f"Restore error: {e.code}")
        raise HTTPException(
            status_code=e.http_status,
            detail=e.to_dict()
        )


@router.post(
    "/restore-batch",
    response_model=BatchRestoreResponse,
    summary="Restore multiple media from trash",
    responses={
        200: {"description": "Batch restore completed"},
    }
)
async def restore_batch(
    request: BatchRestoreRequest,
    service: MediaService = Depends(get_media_service)
):
    """Restore multiple media items from trash"""
    try:
        restored, failed = await service.restore_batch(request.media_ids)
        logger.info(f"Batch restore: {restored}/{len(request.media_ids)} succeeded")
        return BatchRestoreResponse(
            total_requested=len(request.media_ids),
            restored_count=restored,
            failed_count=len(failed),
            failed_media_ids=failed
        )
    except Exception as e:
        logger.error(f"Batch restore error: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch restore failed")


@router.get(
    "/trash",
    response_model=MediaTrashListResponse,
    summary="List media in trash",
    responses={
        200: {"description": "Trash media list"},
    }
)
async def get_trash(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, gt=0, le=100),
    service: MediaService = Depends(get_media_service)
):
    """Get paginated list of media in trash with purge eligibility"""
    try:
        media_list, total = await service.get_trash(skip, limit)

        items = []
        for media in media_list:
            from datetime import datetime, timezone, timedelta
            if media.trash_at:
                trash_duration = datetime.now(timezone.utc) - media.trash_at
                thirty_days = timedelta(days=30)
                days_until_purge = max(0, (thirty_days - trash_duration).days)
                eligible = days_until_purge == 0
            else:
                days_until_purge = 30
                eligible = False

            items.append(MediaTrashResponse(
                id=media.id,
                filename=media.filename,
                file_size=media.file_size,
                media_type=media.media_type,
                trash_at=media.trash_at,
                days_until_purge=days_until_purge,
                eligible_for_purge=eligible
            ))

        return MediaTrashListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Trash query error: {str(e)}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.post(
    "/purge-expired",
    response_model=PurgeExpiredResponse,
    summary="Auto-purge expired media",
    responses={
        200: {"description": "Purge completed"},
    }
)
async def purge_expired_media(
    request: PurgeExpiredMediaRequest = None,
    service: MediaService = Depends(get_media_service)
):
    """Hard delete all media that has been in trash for 30+ days

    Note: This operation is irreversible!
    """
    try:
        if request and request.dry_run:
            # Just count, don't delete
            eligible = await service.repository.find_eligible_for_purge()
            total_size = sum(m.file_size for m in eligible)
            logger.info(f"Dry run: {len(eligible)} items would be purged")
            return PurgeExpiredResponse(
                purged_count=len(eligible),
                purged_size_bytes=total_size,
                remaining_trash_count=0
            )

        purged_count, total_freed = await service.purge_expired()
        remaining_trash = await service.get_trash_count()

        logger.info(f"Purged {purged_count} items ({total_freed} bytes)")
        return PurgeExpiredResponse(
            purged_count=purged_count,
            purged_size_bytes=total_freed,
            remaining_trash_count=remaining_trash
        )

    except Exception as e:
        logger.error(f"Purge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Purge failed")


@router.get(
    "/{entity_type}/{entity_id}",
    response_model=EntityMediaListResponse,
    summary="Get media for entity",
    responses={
        200: {"description": "Media list for entity"},
    }
)
async def get_entity_media(
    entity_type: str,
    entity_id: UUID,
    service: MediaService = Depends(get_media_service)
):
    """Get all media associated with a specific entity (Book/Bookshelf/Block)"""
    try:
        # Convert string to enum
        entity_enum = EntityTypeForMedia[entity_type.upper()]

        media_list = await service.get_entity_media(entity_enum, entity_id)

        return EntityMediaListResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            media_items=[MediaResponse.model_validate(m) for m in media_list],
            count=len(media_list)
        )

    except KeyError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid entity type: {entity_type}"
        )
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.post(
    "/{media_id}/associate",
    status_code=204,
    summary="Associate media with entity",
    responses={
        204: {"description": "Association created"},
        404: {"model": ErrorResponse, "description": "Media not found"},
    }
)
async def associate_media(
    media_id: UUID,
    request: AssociateMediaRequest,
    service: MediaService = Depends(get_media_service)
):
    """Link media to an entity (Book/Bookshelf/Block)"""
    try:
        entity_enum = EntityTypeForMedia[request.entity_type.upper()]
        await service.associate_with_entity(media_id, entity_enum, request.entity_id)
        logger.info(f"Media {media_id} associated with {request.entity_type} {request.entity_id}")
    except KeyError:
        raise HTTPException(status_code=422, detail="Invalid entity type")
    except MediaException as e:
        logger.warning(f"Association error: {e.code}")
        raise HTTPException(
            status_code=e.http_status,
            detail=e.to_dict()
        )


@router.delete(
    "/{media_id}/disassociate",
    status_code=204,
    summary="Remove media association",
    responses={
        204: {"description": "Association removed"},
    }
)
async def disassociate_media(
    media_id: UUID,
    request: DisassociateMediaRequest,
    service: MediaService = Depends(get_media_service)
):
    """Remove link between media and entity"""
    try:
        entity_enum = EntityTypeForMedia[request.entity_type.upper()]
        await service.disassociate_from_entity(media_id, entity_enum, request.entity_id)
        logger.info(f"Media {media_id} disassociated from {request.entity_type} {request.entity_id}")
    except KeyError:
        raise HTTPException(status_code=422, detail="Invalid entity type")
    except Exception as e:
        logger.error(f"Disassociation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Operation failed")
