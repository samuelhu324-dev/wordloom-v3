"""Media Router mappers

Pure mapping utilities between HTTP adapter DTOs and application input commands.
No IO should happen here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import UUID

from api.app.modules.media.application.ports.input import (
    AssociateMediaCommand,
    DeleteMediaCommand,
    DisassociateMediaCommand,
    PurgeMediaCommand,
    RestoreMediaCommand,
    UpdateMediaMetadataCommand,
    UploadImageCommand,
    UploadVideoCommand,
)
from api.app.modules.media.domain import EntityTypeForMedia, MediaMimeType


_MIME_ALIAS_MAP: dict[str, MediaMimeType] = {
    "image/jpg": MediaMimeType.JPEG,
}

_EXTENSION_MIME_MAP: dict[str, MediaMimeType] = {
    ".jpg": MediaMimeType.JPEG,
    ".jpeg": MediaMimeType.JPEG,
    ".png": MediaMimeType.PNG,
    ".webp": MediaMimeType.WEBP,
    ".gif": MediaMimeType.GIF,
    ".mp4": MediaMimeType.MP4,
    ".webm": MediaMimeType.WEBM,
    ".ogg": MediaMimeType.OGG,
}


def resolve_media_mime(content_type: Optional[str], filename: Optional[str]) -> MediaMimeType:
    ct = (content_type or "").lower()
    if ct in _MIME_ALIAS_MAP:
        return _MIME_ALIAS_MAP[ct]
    if ct:
        try:
            return MediaMimeType(ct)
        except ValueError:
            pass

    suffix = Path(filename or "").suffix.lower()
    if suffix in _EXTENSION_MIME_MAP:
        return _EXTENSION_MIME_MAP[suffix]

    raise ValueError("Unsupported media type")


def to_upload_image_command(
    *,
    filename: str,
    content_type: Optional[str],
    file_size: int,
    storage_key: str,
    user_id: Optional[UUID] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> UploadImageCommand:
    return UploadImageCommand(
        filename=filename,
        mime_type=resolve_media_mime(content_type, filename),
        file_size=file_size,
        storage_key=storage_key,
        user_id=user_id,
        width=width,
        height=height,
    )


def to_upload_video_command(
    *,
    filename: str,
    content_type: Optional[str],
    file_size: int,
    storage_key: str,
    user_id: Optional[UUID] = None,
    duration_ms: Optional[int] = None,
) -> UploadVideoCommand:
    return UploadVideoCommand(
        filename=filename,
        mime_type=resolve_media_mime(content_type, filename),
        file_size=file_size,
        storage_key=storage_key,
        user_id=user_id,
        duration_ms=duration_ms,
    )


def to_update_media_metadata_command(
    *,
    media_id: UUID,
    width: Optional[int],
    height: Optional[int],
    duration_ms: Optional[int],
) -> UpdateMediaMetadataCommand:
    return UpdateMediaMetadataCommand(
        media_id=media_id,
        width=width,
        height=height,
        duration_ms=duration_ms,
    )


def to_associate_media_command(*, media_id: UUID, entity_type: str, entity_id: UUID) -> AssociateMediaCommand:
    return AssociateMediaCommand(
        media_id=media_id,
        entity_type=EntityTypeForMedia(entity_type),
        entity_id=entity_id,
    )


def to_disassociate_media_command(
    *, media_id: UUID, entity_type: str, entity_id: UUID
) -> DisassociateMediaCommand:
    return DisassociateMediaCommand(
        media_id=media_id,
        entity_type=EntityTypeForMedia(entity_type),
        entity_id=entity_id,
    )


def to_delete_media_command(*, media_id: UUID) -> DeleteMediaCommand:
    return DeleteMediaCommand(media_id=media_id)


def to_restore_media_command(*, media_id: UUID) -> RestoreMediaCommand:
    return RestoreMediaCommand(media_id=media_id)


def to_purge_media_command(*, media_id: UUID, force: bool) -> PurgeMediaCommand:
    return PurgeMediaCommand(media_id=media_id, force=force)
