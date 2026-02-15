# Library Router - FastAPI routes for Library endpoints

import logging
import os
from pathlib import Path as FilePath
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Path as FastAPIPath, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError

# Application layer imports
from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.update_library import UpdateLibraryUseCase, UpdateLibraryRequest
from api.app.modules.library.application.use_cases.upload_library_cover import (
    UploadLibraryCoverOutcome,
    UploadLibraryCoverRequest,
    UploadLibraryCoverUseCase,
)
from api.app.modules.library.application.use_cases.delete_library import DeleteLibraryUseCase
from api.app.modules.library.application.use_cases.record_library_view import RecordLibraryViewUseCase
from api.app.modules.library.application.use_cases.list_library_tags import ListLibraryTagsUseCase
from api.app.modules.library.application.use_cases.replace_library_tags import ReplaceLibraryTagsUseCase
from api.app.modules.library.application.ports.input import (
    CreateLibraryRequest,
    CreateLibraryResponse,
    GetLibraryRequest,
    GetLibraryResponse,
    DeleteLibraryRequest,
    RecordLibraryViewRequest,
    ListLibraryTagsRequest,
    ReplaceLibraryTagsRequest,
)
from api.app.modules.library.application.ports.output import LibrarySort

# Infrastructure imports
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.storage.bookshelf_repository_impl import SQLAlchemyBookshelfRepository
from infra.storage.library_tag_association_repository_impl import (
    SQLAlchemyLibraryTagAssociationRepository,
)
from infra.database import get_db_session

# Shared infrastructure (EventBus)
from api.app.shared.events import EventBus

# Domain exceptions
from api.app.modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    InvalidLibraryNameError,
    LibraryException,
    DomainException,
)

# Schemas
from api.app.modules.library.schemas import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryDetailResponse,
    LibraryStatus,
    LibraryTagSummary,
    LibraryTagsUpdate,
    LibraryTagsResponse,
    ErrorDetail,
)

# Cross-module dependencies
from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.media.domain import MediaMimeType
from api.app.modules.media.exceptions import (
    InvalidDimensionsError,
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    MediaOperationError,
    StorageQuotaExceededError,
)

# Security
from api.app.config.security import get_current_actor, get_current_user_id
from api.app.shared.actor import Actor
from api.app.config.setting import get_settings

# Storage
from infra.storage.storage_manager import LocalStorageStrategy, StorageManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["libraries"],
    responses={
        404: {"description": "Library not found", "model": ErrorDetail},
        409: {"description": "Conflict", "model": ErrorDetail},
        422: {"description": "Validation error", "model": ErrorDetail},
    },
)

_BACKEND_ROOT = FilePath(__file__).resolve().parents[5]
_STORAGE_ROOT = FilePath(os.getenv("WORDLOOM_STORAGE_ROOT", _BACKEND_ROOT / "storage"))
_library_cover_storage = StorageManager(LocalStorageStrategy(str(_STORAGE_ROOT)))
_settings = get_settings()

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


async def _load_library_tags(
    session: AsyncSession,
    library_ids: List[UUID],
) -> tuple[dict[UUID, List[LibraryTagSummary]], dict[UUID, int]]:
    """Fetch Option A tag chips using the dedicated use case."""

    if not library_ids:
        return {}, {}

    repository = SQLAlchemyLibraryTagAssociationRepository(session)
    use_case = ListLibraryTagsUseCase(repository)
    try:
        response = await use_case.execute(
            ListLibraryTagsRequest(library_ids=library_ids, limit_per_library=3)
        )
    except ProgrammingError as exc:
        # PostgreSQL 42P01: relation does not exist (migration not applied yet)
        if getattr(exc.orig, "pgcode", "") == "42P01":
            logger.warning(
                "tag_associations table missing (run migration 020_create_tag_associations_table.sql); "
                "falling back to empty tag payloads"
            )
            await session.rollback()
            return {}, {}
        raise

    tags_map: dict[UUID, List[LibraryTagSummary]] = {}
    for library_id, chips in response.tag_map.items():
        tags_map[library_id] = [
            LibraryTagSummary(id=chip.id, name=chip.name, color=chip.color, description=chip.description)
            for chip in chips
        ]

    return tags_map, response.tag_totals


async def _build_single_library_tags_response(
    use_case: ListLibraryTagsUseCase,
    session: AsyncSession,
    library_id: UUID,
    *,
    limit: int = 3,
    include_tag_ids: bool = True,
) -> LibraryTagsResponse:
    try:
        uc_response = await use_case.execute(
            ListLibraryTagsRequest(
                library_ids=[library_id],
                limit_per_library=limit,
                include_tag_ids=include_tag_ids,
            )
        )
    except ProgrammingError as exc:
        if getattr(exc.orig, "pgcode", "") == "42P01":
            logger.warning(
                "tag_associations table missing (run migration 020_create_tag_associations_table.sql); "
                "falling back to empty tag payloads"
            )
            await session.rollback()
            return LibraryTagsResponse(
                library_id=library_id,
                tag_ids=[],
                tags=[],
                tag_total_count=0,
            )
        raise

    chips = [
        LibraryTagSummary(id=chip.id, name=chip.name, color=chip.color, description=chip.description)
        for chip in uc_response.tag_map.get(library_id, [])
    ]
    tag_ids = uc_response.tag_id_map.get(library_id, [])
    total = uc_response.tag_totals.get(
        library_id,
        len(tag_ids) if tag_ids else len(chips),
    )

    return LibraryTagsResponse(
        library_id=library_id,
        tag_ids=tag_ids,
        tags=chips,
        tag_total_count=total,
    )


def _resolve_media_mime(upload: UploadFile) -> MediaMimeType:
    content_type = (upload.content_type or "").lower()
    if content_type in _MIME_ALIAS_MAP:
        return _MIME_ALIAS_MAP[content_type]
    if content_type:
        try:
            return MediaMimeType(content_type)
        except ValueError:
            pass

    extension = FilePath(upload.filename or "").suffix.lower()
    if extension in _EXTENSION_MIME_MAP:
        return _EXTENSION_MIME_MAP[extension]
    raise ValueError("Unsupported image type")


def _normalize_filename(original: Optional[str], mime_type: MediaMimeType) -> str:
    extension = FilePath(original or "").suffix.lower() or _MIME_DEFAULT_EXTENSION.get(mime_type, ".img")
    stem = FilePath(original or "library-cover").stem or "library-cover"
    safe_stem = stem.replace(" ", "_")
    return f"{safe_stem}{extension}"


def _build_library_detail_response(
    uc_response,
    tags: Optional[List[LibraryTagSummary]] = None,
    tag_total_count: int = 0,
) -> LibraryDetailResponse:
    status = LibraryStatus.ACTIVE
    if getattr(uc_response, "is_deleted", False):
        status = LibraryStatus.DELETED
    elif getattr(uc_response, "archived_at", None):
        status = LibraryStatus.ARCHIVED

    tag_payload = tags or []

    return LibraryDetailResponse(
        id=uc_response.library_id,
        user_id=uc_response.user_id,
        name=uc_response.name,
        description=getattr(uc_response, "description", None),
        cover_media_id=getattr(uc_response, "cover_media_id", None),
        theme_color=getattr(uc_response, "theme_color", None),
        created_at=uc_response.created_at,
        updated_at=uc_response.updated_at,
        bookshelf_count=0,
        basement_bookshelf_id=uc_response.basement_bookshelf_id,
        status=status,
        pinned=getattr(uc_response, "pinned", False),
        pinned_order=getattr(uc_response, "pinned_order", None),
        archived_at=getattr(uc_response, "archived_at", None),
        last_activity_at=getattr(uc_response, "last_activity_at", uc_response.updated_at),
        views_count=getattr(uc_response, "views_count", 0),
        last_viewed_at=getattr(uc_response, "last_viewed_at", None),
        tags=tag_payload,
        tag_total_count=tag_total_count,
    )


async def get_create_library_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[CreateLibraryUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryRepository(session)
    bookshelf_repository = SQLAlchemyBookshelfRepository(session)
    event_bus = EventBus()
    return (
        CreateLibraryUseCase(
            repository=repository,
            bookshelf_repository=bookshelf_repository,
            event_bus=event_bus,
        ),
        session,
    )


async def get_get_library_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[GetLibraryUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryRepository(session)
    return GetLibraryUseCase(repository=repository), session


async def get_update_library_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[UpdateLibraryUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryRepository(session)
    return UpdateLibraryUseCase(repository=repository), session


async def get_delete_library_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[DeleteLibraryUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryRepository(session)
    event_bus = EventBus()
    return DeleteLibraryUseCase(repository=repository, event_bus=event_bus), session


async def get_record_library_view_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[RecordLibraryViewUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryRepository(session)
    return RecordLibraryViewUseCase(repository=repository), session


async def get_list_library_tags_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[ListLibraryTagsUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryTagAssociationRepository(session)
    return ListLibraryTagsUseCase(repository), session


async def get_replace_library_tags_usecase(
    session: AsyncSession = Depends(get_db_session),
) -> tuple[ReplaceLibraryTagsUseCase, AsyncSession]:
    repository = SQLAlchemyLibraryTagAssociationRepository(session)
    return ReplaceLibraryTagsUseCase(repository), session

def _handle_domain_exception(exc: DomainException) -> HTTPException:
    error_detail = exc.to_dict() if hasattr(exc, "to_dict") else {"message": str(exc)}
    return HTTPException(
        status_code=exc.http_status if hasattr(exc, "http_status") else 500,
        detail=error_detail,
    )

@router.post("", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library(
    request: LibraryCreate,
    user_id: UUID = Depends(get_current_user_id),
    use_case_bundle: tuple[CreateLibraryUseCase, AsyncSession] = Depends(get_create_library_usecase),
) -> LibraryResponse:
    try:
        use_case, _session = use_case_bundle
        uc_request = CreateLibraryRequest(
            user_id=user_id,
            name=request.name,
            description=request.description,
            theme_color=request.theme_color,
        )
        uc_response = await use_case.execute(uc_request)
        return LibraryResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            description=uc_response.description,
            cover_media_id=None,
            theme_color=uc_response.theme_color,
            created_at=uc_response.created_at,
            updated_at=uc_response.created_at,  # Use created_at for newly created library
            pinned=uc_response.pinned,
            pinned_order=uc_response.pinned_order,
            archived_at=uc_response.archived_at,
            last_activity_at=uc_response.last_activity_at,
            views_count=uc_response.views_count,
            last_viewed_at=uc_response.last_viewed_at,
            tags=[],
            tag_total_count=0,
            basement_bookshelf_id=uc_response.basement_bookshelf_id,
        )
    except (LibraryAlreadyExistsError, InvalidLibraryNameError, LibraryException) as exc:
        raise _handle_domain_exception(exc)

@router.get("", response_model=list[LibraryResponse])
async def list_libraries(
    session: AsyncSession = Depends(get_db_session),
    debug: bool = Query(False, description="Include diagnostic headers when true"),
    query: Optional[str] = Query(None, description="Fuzzy search on name/description (case-insensitive). Empty = list all"),
    sort: LibrarySort = Query(LibrarySort.LAST_ACTIVITY_DESC, description="Sort order: last_activity|created|name|views"),
    include_archived: bool = Query(False, description="Include archived libraries in response"),
    pinned_first: bool = Query(True, description="Whether to keep pinned libraries before others"),
) -> list[LibraryResponse]:
    """列出所有库（单用户模式）并支持基本搜索。

    - ?query= 触发 name/description ILIKE 模糊匹配；空或缺省返回全部
    - 后续可扩展 pagination / sorting / tag filtering
    """
    repository = SQLAlchemyLibraryRepository(session)
    try:
        libraries = await repository.list_overview(
            query=query,
            include_archived=include_archived,
            sort=sort,
            pinned_first=pinned_first,
        )
    except Exception as exc:
        logger.exception("List libraries failed")
        raise HTTPException(status_code=500, detail={"message": "Failed to list libraries", "error": str(exc), "query": query})

    tags_map, tag_totals = await _load_library_tags(session, [lib.id for lib in libraries])

    responses = [
        LibraryResponse(
            id=lib.id,
            user_id=lib.user_id,
            name=lib.name.value,
            description=getattr(lib, 'description', None),
            cover_media_id=getattr(lib, 'cover_media_id', None),
            theme_color=getattr(lib, 'theme_color', None),
            created_at=lib.created_at,
            updated_at=lib.updated_at,
            pinned=getattr(lib, 'pinned', False),
            pinned_order=getattr(lib, 'pinned_order', None),
            archived_at=getattr(lib, 'archived_at', None),
            last_activity_at=getattr(lib, 'last_activity_at'),
            views_count=getattr(lib, 'views_count', 0),
            last_viewed_at=getattr(lib, 'last_viewed_at', None),
            tags=tags_map.get(lib.id, []),
            tag_total_count=tag_totals.get(lib.id, len(tags_map.get(lib.id, []))),
            basement_bookshelf_id=getattr(lib, 'basement_bookshelf_id', None),
        )
        for lib in libraries
    ]

    if debug:
        from fastapi.responses import JSONResponse
        headers = {
            "X-Debug-Library-Count": str(len(responses)),
            "X-Debug-Query-Used": "1" if query else "0",
        }
        return JSONResponse(content=[r.dict() for r in responses], headers=headers)
    return responses

@router.post("/{library_id}/views", response_model=LibraryResponse, status_code=status.HTTP_202_ACCEPTED)
async def record_library_view(
    library_id: UUID = FastAPIPath(...),
    use_case_bundle: tuple[RecordLibraryViewUseCase, AsyncSession] = Depends(get_record_library_view_usecase),
) -> LibraryResponse:
    try:
        use_case, session = use_case_bundle
        uc_response = await use_case.execute(RecordLibraryViewRequest(library_id=library_id))
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

    tags_map, tag_totals = await _load_library_tags(session, [uc_response.library_id])

    return LibraryResponse(
        id=uc_response.library_id,
        user_id=uc_response.user_id,
        name=uc_response.name,
        description=getattr(uc_response, "description", None),
        cover_media_id=getattr(uc_response, "cover_media_id", None),
        created_at=uc_response.created_at,
        updated_at=uc_response.updated_at,
        pinned=uc_response.pinned,
        pinned_order=uc_response.pinned_order,
        archived_at=uc_response.archived_at,
        last_activity_at=uc_response.last_activity_at,
        views_count=uc_response.views_count,
        last_viewed_at=uc_response.last_viewed_at,
        tags=tags_map.get(uc_response.library_id, []),
        tag_total_count=tag_totals.get(uc_response.library_id, len(tags_map.get(uc_response.library_id, []))),
        theme_color=getattr(uc_response, 'theme_color', None),
        basement_bookshelf_id=uc_response.basement_bookshelf_id,
    )

@router.get("/{library_id}", response_model=LibraryDetailResponse)
async def get_library(
    library_id: UUID = FastAPIPath(...),
    actor: Actor = Depends(get_current_actor),
    use_case_bundle: tuple[GetLibraryUseCase, AsyncSession] = Depends(get_get_library_usecase),
) -> LibraryDetailResponse:
    try:
        use_case, session = use_case_bundle
        uc_request = GetLibraryRequest(
            library_id=library_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        uc_response = await use_case.execute(uc_request)
        tags_map, tag_totals = await _load_library_tags(session, [uc_response.library_id])
        return _build_library_detail_response(
            uc_response,
            tags_map.get(uc_response.library_id, []),
            tag_totals.get(uc_response.library_id, len(tags_map.get(uc_response.library_id, []))),
        )
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.get("/user/{user_id}", response_model=LibraryDetailResponse)
async def get_user_library(
    user_id: UUID = FastAPIPath(...),
    use_case: GetLibraryUseCase = Depends(get_get_library_usecase),
) -> LibraryDetailResponse:
    # Deprecated under multi-library. Use GET /libraries with auth or filters.
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
            "message": "Endpoint deprecated: use GET /libraries (flat endpoint) with query filters",
            "deprecated": True,
        },
    )

@router.post(
    "/{library_id}/cover",
    response_model=LibraryDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传并设置 Library 封面",
)
async def upload_library_cover(
    request: Request,
    library_id: UUID = FastAPIPath(...),
    file: UploadFile = File(..., description="封面图片文件 (JPEG/PNG/WEBP/GIF)"),
    user_id: UUID = Depends(get_current_user_id),
    di: DIContainer = Depends(get_di_container),
    session: AsyncSession = Depends(get_db_session),
) -> LibraryDetailResponse:
    correlation_id = getattr(getattr(request, "state", None), "correlation_id", None)

    def _emit_usecase_outcome(
        *,
        outcome: str,
        status_code: int,
        media_id: Optional[UUID] = None,
        error: Optional[object] = None,
    ) -> None:
        logger.info(
            {
                "event": "usecase.outcome",
                "operation": "library.cover.bind",
                "layer": "handler",
                "outcome": outcome,
                "status_code": status_code,
                "correlation_id": correlation_id,
                "entity_type": "library",
                "entity_id": str(library_id),
                "media_id": str(media_id) if media_id else None,
                "error": error,
            }
        )

    logger.info(f"[upload_library_cover] START library_id={library_id}, file={file.filename}")
    file_bytes = await file.read()

    use_case = UploadLibraryCoverUseCase(
        get_library_use_case=di.get_get_library_use_case(),
        upload_image_use_case=di.get_upload_image_use_case(),
        update_library_use_case=di.get_update_library_use_case(),
        storage=_library_cover_storage,
        allow_dev_library_owner_override=_settings.allow_dev_library_owner_override,
    )

    result = await use_case.execute(
        UploadLibraryCoverRequest(
            library_id=library_id,
            actor_user_id=user_id,
            file_bytes=file_bytes,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    )

    if result.outcome == UploadLibraryCoverOutcome.SUCCESS:
        _emit_usecase_outcome(
            outcome="success",
            status_code=status.HTTP_201_CREATED,
            media_id=result.media_id,
        )
        tags_map, tag_totals = await _load_library_tags(session, [library_id])
        return _build_library_detail_response(
            result.library,
            tags_map.get(library_id, []),
            tag_totals.get(library_id, len(tags_map.get(library_id, []))),
        )

    if result.outcome == UploadLibraryCoverOutcome.NOT_FOUND:
        _emit_usecase_outcome(
            outcome="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
            media_id=result.media_id,
            error=str(result.error) if result.error else None,
        )
        if isinstance(result.error, LibraryException):
            raise _handle_domain_exception(result.error)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")

    if result.outcome == UploadLibraryCoverOutcome.FORBIDDEN:
        _emit_usecase_outcome(
            outcome="forbidden",
            status_code=status.HTTP_403_FORBIDDEN,
            media_id=result.media_id,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if result.outcome == UploadLibraryCoverOutcome.REJECTED_EMPTY:
        _emit_usecase_outcome(outcome="validation_failed", status_code=status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="封面文件不能为空")

    if result.outcome == UploadLibraryCoverOutcome.REJECTED_MIME:
        _emit_usecase_outcome(outcome="validation_failed", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的图片类型")

    if result.outcome == UploadLibraryCoverOutcome.REJECTED_TOO_LARGE:
        _emit_usecase_outcome(outcome="validation_failed", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "FILE_SIZE_TOO_LARGE",
                "message": "封面文件过大",
                "details": {"max_size": UploadLibraryCoverUseCase.MAX_IMAGE_SIZE},
            },
        )

    if result.outcome == UploadLibraryCoverOutcome.STORAGE_SAVE_FAILED:
        _emit_usecase_outcome(
            outcome="error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="cover_storage_failed",
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="无法保存封面文件")

    if result.outcome == UploadLibraryCoverOutcome.MEDIA_VALIDATION_FAILED:
        _emit_usecase_outcome(
            outcome="validation_failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=result.error,
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.error)

    if result.outcome == UploadLibraryCoverOutcome.QUOTA_EXCEEDED:
        _emit_usecase_outcome(
            outcome="error",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error=result.error,
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=result.error)

    if result.outcome == UploadLibraryCoverOutcome.UPDATE_FAILED:
        _emit_usecase_outcome(
            outcome="error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_id=result.media_id,
            error=str(result.error) if result.error else None,
        )
        if isinstance(result.error, LibraryException):
            raise _handle_domain_exception(result.error)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="封面绑定失败")

    # MEDIA_OPERATION_FAILED and any other fallback
    _emit_usecase_outcome(
        outcome="error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_id=result.media_id,
        error=result.error,
    )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="封面上传失败")

@router.patch("/{library_id}", response_model=LibraryDetailResponse)
async def patch_library(
    library_id: UUID = FastAPIPath(...),
    request: LibraryUpdate = None,
    actor: Actor = Depends(get_current_actor),
    use_case_bundle: tuple[UpdateLibraryUseCase, AsyncSession] = Depends(get_update_library_usecase),
) -> LibraryDetailResponse:
    try:
        use_case, session = use_case_bundle
        cover_media_field_provided = bool(request and "cover_media_id" in request.model_fields_set)
        theme_color_field_provided = bool(request and "theme_color" in request.model_fields_set)
        update_req = UpdateLibraryRequest(
            library_id=library_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
            name=request.name if request else None,
            description=request.description if request else None,
            cover_media_id=request.cover_media_id if cover_media_field_provided else None,
            cover_media_id_provided=cover_media_field_provided,
            theme_color=request.theme_color if theme_color_field_provided else None,
            theme_color_provided=theme_color_field_provided,
            pinned=request.pinned if request else None,
            pinned_order=request.pinned_order if request else None,
            archived=request.archived if request else None,
        )
        uc_response = await use_case.execute(update_req)
        tags_map, tag_totals = await _load_library_tags(session, [library_id])
        return _build_library_detail_response(
            uc_response,
            tags_map.get(library_id, []),
            tag_totals.get(library_id, len(tags_map.get(library_id, []))),
        )
    except LibraryException as exc:
        raise _handle_domain_exception(exc)


@router.get("/{library_id}/tags", response_model=LibraryTagsResponse)
async def get_library_tags(
    library_id: UUID = FastAPIPath(...),
    limit: int = Query(
        3,
        ge=0,
        le=25,
        description="Maximum number of Option A chips to return",
    ),
    use_case_bundle: tuple[ListLibraryTagsUseCase, AsyncSession] = Depends(get_list_library_tags_usecase),
) -> LibraryTagsResponse:
    use_case, session = use_case_bundle

    repository = SQLAlchemyLibraryRepository(session)
    if not await repository.exists(library_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Library not found", "library_id": str(library_id)},
        )

    return await _build_single_library_tags_response(
        use_case,
        session,
        library_id,
        limit=limit,
        include_tag_ids=True,
    )


@router.put("/{library_id}/tags", response_model=LibraryTagsResponse)
async def replace_library_tags(
    library_id: UUID = FastAPIPath(...),
    payload: LibraryTagsUpdate = ...,
    limit: int = Query(
        3,
        ge=0,
        le=25,
        description="Maximum number of Option A chips to return",
    ),
    user_id: UUID = Depends(get_current_user_id),
    use_case_bundle: tuple[ReplaceLibraryTagsUseCase, AsyncSession] = Depends(get_replace_library_tags_usecase),
) -> LibraryTagsResponse:
    use_case, session = use_case_bundle

    repository = SQLAlchemyLibraryRepository(session)
    library = await repository.get_by_id(library_id)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Library not found", "library_id": str(library_id)},
        )

    if (not _settings.allow_dev_library_owner_override) and library.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    try:
        await use_case.execute(
            ReplaceLibraryTagsRequest(
                library_id=library_id,
                tag_ids=payload.tag_ids,
                actor_id=user_id,
            )
        )
    except ProgrammingError as exc:
        if getattr(exc.orig, "pgcode", "") == "42P01":
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": "tag_associations table missing (run migration 020_create_tag_associations_table.sql)",
                    "code": "TAG_TABLE_MISSING",
                },
            )
        raise

    list_use_case = ListLibraryTagsUseCase(SQLAlchemyLibraryTagAssociationRepository(session))
    return await _build_single_library_tags_response(
        list_use_case,
        session,
        library_id,
        limit=limit,
        include_tag_ids=True,
    )

@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(
    library_id: UUID = FastAPIPath(...),
    actor: Actor = Depends(get_current_actor),
    use_case_bundle: tuple[DeleteLibraryUseCase, AsyncSession] = Depends(get_delete_library_usecase),
) -> None:
    try:
        use_case, _session = use_case_bundle
        uc_request = DeleteLibraryRequest(
            library_id=library_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=(not _settings.allow_dev_library_owner_override),
        )
        await use_case.execute(uc_request)
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "library"}

@router.get("/debug/meta", tags=["libraries"], summary="Diagnostic library metadata")
async def libraries_meta(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return minimal metadata (count, user id) to distinguish empty from failure."""
    repository = SQLAlchemyLibraryRepository(session)
    try:
        libraries = await repository.list_by_user_id(user_id)
    except Exception as exc:
        logger.exception("libraries_meta failed")
        raise HTTPException(status_code=500, detail={"message": "Failed to fetch meta", "error": str(exc)})
    return {
        "user_id": str(user_id),
        "count": len(libraries),
        "has_libraries": len(libraries) > 0,
    }

@router.get("/deleted", response_model=list[LibraryResponse])
async def list_deleted_libraries(limit: int | None = None) -> list[LibraryResponse]:
    """List soft-deleted libraries (placeholder).

    Frontend currently probes /libraries/deleted?limit=1 which returned 404.
    This placeholder returns empty list until soft-delete lifecycle implemented.
    Args:
        limit: optional limit for future pagination.
    Returns:
        Empty list (no deleted libraries yet)
    """
    return []

@router.get("/test/create-sample", tags=["test"])
async def create_sample_library(session: AsyncSession = Depends(get_db_session)) -> LibraryResponse:
    """
    Test endpoint: Create a sample library
    For development/testing only
    """
    try:
        repository = SQLAlchemyLibraryRepository(session)
        bookshelf_repository = SQLAlchemyBookshelfRepository(session)
        event_bus = EventBus()
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        uc_request = CreateLibraryRequest(user_id=user_id, name="Test Library")
        use_case = CreateLibraryUseCase(
            repository=repository,
            bookshelf_repository=bookshelf_repository,
            event_bus=event_bus,
        )
        uc_response = await use_case.execute(uc_request)
        return LibraryResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            description=uc_response.description,
            cover_media_id=uc_response.cover_media_id,
            theme_color=uc_response.theme_color,
            created_at=uc_response.created_at,
            updated_at=uc_response.updated_at,
            pinned=uc_response.pinned,
            pinned_order=uc_response.pinned_order,
            archived_at=uc_response.archived_at,
            last_activity_at=uc_response.last_activity_at,
            views_count=uc_response.views_count,
            last_viewed_at=uc_response.last_viewed_at,
            tags=[],
            tag_total_count=0,
            basement_bookshelf_id=uc_response.basement_bookshelf_id,
        )
    except Exception as exc:
        logger.error(f"Error creating sample library: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/debug/all", tags=["libraries"], summary="(保持) 全部库调试列表")
async def list_all_libraries_debug(session: AsyncSession = Depends(get_db_session)) -> list[LibraryResponse]:
    repository = SQLAlchemyLibraryRepository(session)
    try:
        libraries = await repository.list_all()
    except Exception as exc:
        logger.exception("debug all libraries failed")
        raise HTTPException(status_code=500, detail={"message": "debug/all failed", "error": str(exc)})

    if not libraries:
        return []

    tags_map, tag_totals = await _load_library_tags(session, [lib.id for lib in libraries])

    return [
        LibraryResponse(
            id=lib.id,
            user_id=lib.user_id,
            name=lib.name.value,
            description=getattr(lib, "description", None),
            cover_media_id=getattr(lib, "cover_media_id", None),
            theme_color=getattr(lib, "theme_color", None),
            created_at=lib.created_at,
            updated_at=getattr(lib, "updated_at", lib.created_at),
            pinned=getattr(lib, "pinned", False),
            pinned_order=getattr(lib, "pinned_order", None),
            archived_at=getattr(lib, "archived_at", None),
            last_activity_at=getattr(lib, "last_activity_at", lib.created_at),
            views_count=getattr(lib, "views_count", 0),
            last_viewed_at=getattr(lib, "last_viewed_at", None),
            tags=tags_map.get(lib.id, []),
            tag_total_count=tag_totals.get(lib.id, len(tags_map.get(lib.id, []))),
            basement_bookshelf_id=getattr(lib, 'basement_bookshelf_id', None),
        )
        for lib in libraries
    ]

@router.post("/debug/test-upload", tags=["debug"], summary="Debug: Test cover upload")
async def debug_test_upload(
    di: DIContainer = Depends(get_di_container),
) -> dict:
    """Test the upload flow without actual file - for debugging"""
    logger.info("[DEBUG TEST-UPLOAD] START")
    try:
        # Get a library (or create one)
        libraries_uc = di.get_list_libraries_use_case()
        logger.info("[DEBUG TEST-UPLOAD] Got libraries UC")

        return {
            "status": "ok",
            "message": "Debug endpoint working"
        }
    except Exception as e:
        logger.exception("[DEBUG TEST-UPLOAD] Error")
        return {"status": "error", "error": str(e)}


