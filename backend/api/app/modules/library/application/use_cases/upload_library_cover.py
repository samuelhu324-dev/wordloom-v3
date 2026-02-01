"""UploadLibraryCover UseCase (Route A: decision table)

Moves Library cover upload + bind decisions out of the HTTP handler.

Responsibilities:
- Authorization: only owner can upload (unless dev override enabled)
- Validation: non-empty, supported image MIME, max size
- Side effects ordering:
  1) write file to storage
  2) create Media row via UploadImageUseCase
  3) bind library.cover_media_id via UpdateLibraryUseCase
  4) compensate by deleting storage file on failures before (2)

This use case is intentionally outcome-driven (no HTTP exceptions).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path as FilePath
from typing import Optional, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.library.application.ports.input import GetLibraryRequest, GetLibraryResponse
from api.app.modules.library.application.use_cases.update_library import (
    UpdateLibraryRequest,
    UpdateLibraryResponse,
)
from api.app.modules.library.exceptions import LibraryException, LibraryNotFoundError

from api.app.modules.media.domain import MediaMimeType
from api.app.modules.media.exceptions import (
    FileSizeTooLargeError,
    InvalidDimensionsError,
    InvalidMimeTypeError,
    MediaOperationError,
    StorageQuotaExceededError,
)


class ILibraryCoverStorage(Protocol):
    async def save_library_cover(self, content: bytes, library_id: UUID, original_filename: str) -> str: ...

    async def delete_file(self, file_path: str) -> None: ...


class IGetLibraryUseCase(Protocol):
    async def execute(self, request: GetLibraryRequest) -> GetLibraryResponse: ...


class IUploadImageUseCase(Protocol):
    async def execute(
        self,
        *,
        filename: str,
        mime_type: MediaMimeType,
        file_size: int,
        storage_key: str,
        user_id: Optional[UUID] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        ...


class IUpdateLibraryUseCase(Protocol):
    async def execute(self, request: UpdateLibraryRequest) -> UpdateLibraryResponse: ...


class UploadLibraryCoverOutcome(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"

    REJECTED_EMPTY = "rejected_empty"
    REJECTED_MIME = "rejected_mime"
    REJECTED_TOO_LARGE = "rejected_too_large"

    STORAGE_SAVE_FAILED = "storage_save_failed"
    MEDIA_VALIDATION_FAILED = "media_validation_failed"
    QUOTA_EXCEEDED = "quota_exceeded"
    MEDIA_OPERATION_FAILED = "media_operation_failed"
    UPDATE_FAILED = "update_failed"


@dataclass(frozen=True)
class UploadLibraryCoverRequest:
    library_id: UUID
    actor_user_id: UUID
    file_bytes: bytes
    original_filename: Optional[str]
    content_type: Optional[str]


@dataclass(frozen=True)
class UploadLibraryCoverResult:
    outcome: UploadLibraryCoverOutcome
    library: Optional[UpdateLibraryResponse] = None
    media_id: Optional[UUID] = None
    storage_key: Optional[str] = None
    previous_cover_media_id: Optional[UUID] = None
    error: Optional[object] = None


_MIME_ALIAS_MAP = {
    "image/jpg": MediaMimeType.JPEG,
}

_EXTENSION_MIME_MAP = {
    ".jpg": MediaMimeType.JPEG,
    ".jpeg": MediaMimeType.JPEG,
    ".png": MediaMimeType.PNG,
    ".webp": MediaMimeType.WEBP,
    ".gif": MediaMimeType.GIF,
}

_MIME_DEFAULT_EXTENSION = {
    MediaMimeType.JPEG: ".jpg",
    MediaMimeType.PNG: ".png",
    MediaMimeType.WEBP: ".webp",
    MediaMimeType.GIF: ".gif",
}


def _resolve_media_mime(*, content_type: Optional[str], filename: Optional[str]) -> MediaMimeType:
    ct = (content_type or "").lower()
    if ct in _MIME_ALIAS_MAP:
        return _MIME_ALIAS_MAP[ct]
    if ct:
        try:
            return MediaMimeType(ct)
        except ValueError:
            pass

    extension = FilePath(filename or "").suffix.lower()
    if extension in _EXTENSION_MIME_MAP:
        return _EXTENSION_MIME_MAP[extension]

    raise ValueError("Unsupported image type")


def _normalize_filename(original: Optional[str], mime_type: MediaMimeType) -> str:
    extension = FilePath(original or "").suffix.lower() or _MIME_DEFAULT_EXTENSION.get(mime_type, ".img")
    stem = FilePath(original or "library-cover").stem or "library-cover"
    safe_stem = stem.replace(" ", "_")
    return f"{safe_stem}{extension}"


class UploadLibraryCoverUseCase:
    """Outcome-driven use case for uploading + binding a library cover."""

    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB (align with UploadImageUseCase)

    def __init__(
        self,
        *,
        get_library_use_case: IGetLibraryUseCase,
        upload_image_use_case: IUploadImageUseCase,
        update_library_use_case: IUpdateLibraryUseCase,
        storage: ILibraryCoverStorage,
        allow_dev_library_owner_override: bool,
    ):
        self._get_library = get_library_use_case
        self._upload_image = upload_image_use_case
        self._update_library = update_library_use_case
        self._storage = storage
        self._allow_owner_override = allow_dev_library_owner_override

    async def execute(
        self,
        request: UploadLibraryCoverRequest,
        *,
        db_session: Optional[AsyncSession] = None,
    ) -> UploadLibraryCoverResult:
        try:
            library_snapshot = await self._get_library.execute(
                GetLibraryRequest(library_id=request.library_id)
            )
        except LibraryException as exc:
            if isinstance(exc, LibraryNotFoundError):
                return UploadLibraryCoverResult(
                    outcome=UploadLibraryCoverOutcome.NOT_FOUND,
                    error=exc,
                )
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.UPDATE_FAILED,
                error=exc,
            )

        if (not self._allow_owner_override) and library_snapshot.user_id != request.actor_user_id:
            return UploadLibraryCoverResult(outcome=UploadLibraryCoverOutcome.FORBIDDEN)

        if not request.file_bytes:
            return UploadLibraryCoverResult(outcome=UploadLibraryCoverOutcome.REJECTED_EMPTY)

        if len(request.file_bytes) > self.MAX_IMAGE_SIZE:
            return UploadLibraryCoverResult(outcome=UploadLibraryCoverOutcome.REJECTED_TOO_LARGE)

        try:
            mime_type = _resolve_media_mime(
                content_type=request.content_type,
                filename=request.original_filename,
            )
        except ValueError:
            return UploadLibraryCoverResult(outcome=UploadLibraryCoverOutcome.REJECTED_MIME)

        filename = _normalize_filename(request.original_filename, mime_type)

        try:
            storage_key = await self._storage.save_library_cover(
                request.file_bytes,
                request.library_id,
                filename,
            )
        except Exception as exc:
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.STORAGE_SAVE_FAILED,
                error=str(exc),
            )

        tx = None
        if db_session is not None:
            # Route B / experimentation hook:
            # Keep media+library update atomic inside a savepoint. This allows us to
            # rollback the Media insert if binding the Library fails, while leaving
            # the outer request transaction boundary unchanged.
            tx = await db_session.begin_nested()

        try:
            media = await self._upload_image.execute(
                filename=filename,
                mime_type=mime_type,
                file_size=len(request.file_bytes),
                storage_key=storage_key,
                user_id=library_snapshot.user_id,
            )
        except (InvalidMimeTypeError, FileSizeTooLargeError, InvalidDimensionsError) as exc:
            if tx is not None:
                await tx.rollback()
            await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.MEDIA_VALIDATION_FAILED,
                storage_key=storage_key,
                error=getattr(exc, "to_dict", lambda: str(exc))(),
            )
        except StorageQuotaExceededError as exc:
            if tx is not None:
                await tx.rollback()
            await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.QUOTA_EXCEEDED,
                storage_key=storage_key,
                error=getattr(exc, "to_dict", lambda: str(exc))(),
            )
        except MediaOperationError as exc:
            if tx is not None:
                await tx.rollback()
            await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.MEDIA_OPERATION_FAILED,
                storage_key=storage_key,
                error=getattr(exc, "to_dict", lambda: str(exc))(),
            )
        except Exception as exc:
            if tx is not None:
                await tx.rollback()
            await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.MEDIA_OPERATION_FAILED,
                storage_key=storage_key,
                error=str(exc),
            )

        try:
            uc_response = await self._update_library.execute(
                UpdateLibraryRequest(
                    library_id=request.library_id,
                    cover_media_id=getattr(media, "id", None),
                    cover_media_id_provided=True,
                )
            )
        except LibraryException as exc:
            if isinstance(exc, LibraryNotFoundError):
                if tx is not None:
                    await tx.rollback()
                    await self._storage.delete_file(storage_key)
                return UploadLibraryCoverResult(
                    outcome=UploadLibraryCoverOutcome.NOT_FOUND,
                    media_id=getattr(media, "id", None),
                    storage_key=storage_key,
                    error=exc,
                )

            if tx is not None:
                await tx.rollback()
                await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.UPDATE_FAILED,
                media_id=getattr(media, "id", None),
                storage_key=storage_key,
                error=exc,
            )
        except Exception as exc:
            if tx is not None:
                await tx.rollback()
                await self._storage.delete_file(storage_key)
                return UploadLibraryCoverResult(
                    outcome=UploadLibraryCoverOutcome.UPDATE_FAILED,
                    media_id=getattr(media, "id", None),
                    storage_key=storage_key,
                    error=str(exc),
                )

            # Keep behavior consistent with current handler: no cleanup of file/media.
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.UPDATE_FAILED,
                media_id=getattr(media, "id", None),
                storage_key=storage_key,
                error=str(exc),
            )

        if (not self._allow_owner_override) and uc_response.user_id != request.actor_user_id:
            if tx is not None:
                await tx.rollback()
                await self._storage.delete_file(storage_key)
            return UploadLibraryCoverResult(
                outcome=UploadLibraryCoverOutcome.FORBIDDEN,
                library=uc_response,
                media_id=getattr(media, "id", None),
                storage_key=storage_key,
                previous_cover_media_id=getattr(library_snapshot, "cover_media_id", None),
            )

        if tx is not None:
            await tx.commit()

        return UploadLibraryCoverResult(
            outcome=UploadLibraryCoverOutcome.SUCCESS,
            library=uc_response,
            media_id=getattr(media, "id", None),
            storage_key=storage_key,
            previous_cover_media_id=getattr(library_snapshot, "cover_media_id", None),
        )
