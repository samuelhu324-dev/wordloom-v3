"""
Book Router - Hexagonal Architecture Pattern

Implements complete 4-layer architecture with DI chain:
    Layer 1: HTTP validation + permission checks (Router)
    Layer 2: Business logic orchestration (UseCase)
    Layer 3: Persistence abstraction (Repository)
    Layer 4: Data access (ORM/Infrastructure)

Routes (8 total):
    POST   /books                    CreateBookUseCase           (RULE-009/010)
    GET    /books                    ListBooksUseCase            (RULE-009)
    GET    /books/{book_id}          GetBookUseCase              (RULE-009/010)
    PUT    /books/{book_id}          UpdateBookUseCase           (RULE-010)
    DELETE /books/{book_id}          DeleteBookUseCase           (RULE-012 soft-delete)
    PUT    /books/{book_id}/move     MoveBookUseCase             (RULE-011 transfer)
    POST   /books/{book_id}/restore  RestoreBookUseCase          (RULE-013 basement recovery)
    GET    /books/deleted            ListDeletedBooksUseCase     (RULE-012 basement view)

Design Decisions:
- Route prefix is /books (not nested under /bookshelves) to enable cross-bookshelf operations
- bookshelf_id provided in request body/query to enable transfer logic (RULE-011)
- Soft delete via basement bookshelf ID (RULE-012)
- Restoration requires target bookshelf ID (RULE-013)
- Full DIContainer dependency injection chain
- Structured error handling with HTTP status mappings
- Comprehensive logging for observability
"""

import logging
import os
from datetime import datetime
from pathlib import Path as FilePath
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.book.application.ports.input import (
    CreateBookRequest,
    ListBooksRequest,
    GetBookRequest,
    UpdateBookRequest,
    DeleteBookRequest,
    RestoreBookRequest,
    ListDeletedBooksRequest,
    MoveBookRequest,
)
from api.app.modules.book.domain.book import Book as BookAggregate, BookMaturity
from api.app.modules.book.domain.exceptions import (
    BookNotFoundError,
    BookAlreadyExistsError,
    DomainException,
    InvalidBookMoveError,
    BookNotInBasementError,
    InvalidBookMaturityTransitionError,
    InvalidBookDataError,
)
from api.app.modules.book.schemas import BookUpdate
from api.app.modules.book.application.ports.input import (
    RecalculateBookMaturityRequest as RecalcReq,
    GetBookRequest as GetReq,
)
from api.app.modules.media.domain import MediaMimeType
from api.app.modules.media.exceptions import (
    InvalidDimensionsError,
    InvalidMimeTypeError,
    FileSizeTooLargeError,
    MediaOperationError,
    StorageQuotaExceededError,
)
from infra.storage.storage_manager import LocalStorageStrategy, StorageManager
from infra.database.models.library_models import LibraryModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["books"])

_BACKEND_ROOT = FilePath(__file__).resolve().parents[5]
_STORAGE_ROOT = FilePath(os.getenv("WORDLOOM_STORAGE_ROOT", _BACKEND_ROOT / "storage"))
_book_cover_storage = StorageManager(LocalStorageStrategy(str(_STORAGE_ROOT)))

_MIME_ALIAS_MAP = {"image/jpg": MediaMimeType.JPEG}
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
    stem = FilePath(original or "book-cover").stem or "book-cover"
    safe_stem = stem.replace(" ", "_")
    return f"{safe_stem}{extension}"


def _book_allows_custom_cover(book: BookAggregate) -> bool:
    maturity = getattr(book, "maturity", None)
    if isinstance(maturity, str):
        try:
            maturity_enum = BookMaturity(maturity)
        except ValueError:
            return False
    else:
        maturity_enum = maturity
    if maturity_enum != BookMaturity.STABLE:
        return False
    return not bool(getattr(book, "legacy_flag", False))


def _value_or_none(value: Any) -> Any:
    """Extract value from value objects or enums."""
    if value is None:
        return None
    return getattr(value, "value", value)


def _datetime_to_iso(value: Any) -> Optional[str]:
    """Serialize datetime-like values to ISO strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            return str(value)
    return str(value)


def _serialize_book(book: BookAggregate) -> dict:
    """Convert Book aggregate into API-friendly dict."""
    title = _value_or_none(getattr(book, "title", None))
    summary_obj = getattr(book, "summary", None)
    summary = _value_or_none(summary_obj)
    tags_summary = list(getattr(book, "tags_summary", []) or [])

    return {
        "id": getattr(book, "id", None),
        "library_id": getattr(book, "library_id", None),
        "bookshelf_id": getattr(book, "bookshelf_id", None),
        "title": title,
        "summary": summary,
        "cover_icon": getattr(book, "cover_icon", None),
        "cover_media_id": getattr(book, "cover_media_id", None),
        "book_type": getattr(book, "book_type", "normal") or "normal",
        "status": _value_or_none(getattr(book, "status", None)) or "draft",
        "maturity": _value_or_none(getattr(book, "maturity", None)) or "seed",
        "maturity_score": getattr(book, "maturity_score", 0) or 0,
        "legacy_flag": bool(getattr(book, "legacy_flag", False)),
        "manual_maturity_override": bool(getattr(book, "manual_maturity_override", False)),
        "manual_maturity_reason": getattr(book, "manual_maturity_reason", None),
        "is_pinned": bool(getattr(book, "is_pinned", False)),
        "priority": getattr(book, "priority", None),
        "urgency": getattr(book, "urgency", None),
        "due_at": _datetime_to_iso(getattr(book, "due_at", None)),
        "block_count": getattr(book, "block_count", 0) or 0,
        "last_visited_at": _datetime_to_iso(getattr(book, "last_visited_at", None)),
        "visit_count_90d": getattr(book, "visit_count_90d", 0) or 0,
        "soft_deleted_at": _datetime_to_iso(getattr(book, "soft_deleted_at", None)),
        "created_at": _datetime_to_iso(getattr(book, "created_at", None)),
        "updated_at": _datetime_to_iso(getattr(book, "updated_at", None)),
        "tags_summary": tags_summary,
    }


async def _serialize_book_with_theme(book: BookAggregate, di: DIContainer) -> dict:
    payload = _serialize_book(book)
    library_id = payload.get("library_id") or getattr(book, "library_id", None)
    payload["library_theme_color"] = await _fetch_library_theme_color(di, library_id)
    return payload


async def _fetch_library_theme_color(di: DIContainer, library_id: Optional[Any]) -> Optional[str]:
    normalized_id = _normalize_uuid(library_id)
    if not normalized_id:
        return None
    cache = getattr(di, "_library_theme_color_cache", None)
    if cache is None:
        cache = {}
        setattr(di, "_library_theme_color_cache", cache)
    cache_key = str(normalized_id)
    if cache_key in cache:
        return cache[cache_key]
    session_getter = getattr(di, "get_session", None)
    session = None
    if callable(session_getter):
        try:
            session = session_getter()
        except Exception as session_error:
            logger.warning("Failed to access DI session: %%s", session_error)
    if session is None:
        session = getattr(di, "session", None)
    if session is None:
        logger.warning("DI container has no session available for theme lookup")
        cache[cache_key] = None
        return None
    stmt = select(LibraryModel.theme_color).where(LibraryModel.id == normalized_id)
    result = await session.execute(stmt)
    value = result.scalar_one_or_none()
    cache[cache_key] = value
    return value


def _normalize_uuid(value: Optional[Any]) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except Exception:
        return None


def _serialize_response(response: Any) -> Any:
    """Normalize response objects (Domain or Pydantic) into serializable data."""
    if isinstance(response, BookAggregate):
        return _serialize_book(response)
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if isinstance(response, list):
        return [_serialize_response(item) for item in response]
    return response


def _http_status(error: Exception, fallback: int) -> int:
    """Resolve HTTP status from domain error."""
    return getattr(error, "status_code", getattr(error, "http_status", fallback))


def _domain_error_payload(error: Exception, fallback_code: str) -> dict:
    """Build consistent error payload for HTTP responses."""
    if hasattr(error, "to_dict"):
        payload = error.to_dict()
        if not isinstance(payload, dict):
            return {"code": fallback_code, "message": str(error)}
        payload.setdefault("code", getattr(error, "error_code", fallback_code))
        payload.setdefault("message", str(error))
        return payload

    detail = getattr(error, "detail", None)
    code = getattr(error, "error_code", fallback_code)
    if isinstance(detail, dict):
        return {"code": code, "message": str(error), "details": detail}
    if isinstance(detail, str) and detail:
        return {"code": code, "message": detail}
    return {"code": code, "message": str(error)}


# ============================================================================
# Create Book (RULE-009: Unlimited creation, RULE-010: Must belong to shelf)
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    description="Create a new book (RULE-009: Unlimited creation | RULE-010: Must belong to bookshelf)"
)
async def create_book(
    request: CreateBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    try:
        logger.info(
            "Creating book: title='%s' in bookshelf_id=%s",
            request.title,
            request.bookshelf_id,
        )
        use_case = di.get_create_book_use_case()
        book = await use_case.execute(
            bookshelf_id=request.bookshelf_id,
            library_id=request.library_id,
            title=request.title,
            description=request.summary,
            cover_icon=request.cover_icon,
        )
        logger.info("Book created successfully: book_id=%s", getattr(book, "id", None))
        return await _serialize_book_with_theme(book, di)
    except BookAlreadyExistsError as error:
        logger.warning("Book creation failed - already exists: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_409_CONFLICT),
            detail=_domain_error_payload(error, "BOOK_ALREADY_EXISTS"),
        )
    except DomainException as error:
        logger.warning("Book creation failed - validation error: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error creating book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to create book"},
        )


# ============================================================================
# List Books (RULE-009: Unlimited query, RULE-012: Soft-delete filtering)
# ============================================================================

@router.get(
    "",
    response_model=dict,
    summary="List books",
    description="List books with optional filtering (RULE-012: Soft-delete filtering by default)"
)
async def list_books(
    bookshelf_id: Optional[UUID] = Query(None, description="Filter by bookshelf_id"),
    library_id: Optional[UUID] = Query(None, description="Filter by library_id (permission context)"),
    include_deleted: bool = Query(False, description="Include soft-deleted books (RULE-012)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    di: DIContainer = Depends(get_di_container)
):
    """列出书籍 (RULE-012: 默认排除软删除的书籍)

    Args:
        bookshelf_id: Filter by specific bookshelf (optional)
        library_id: Filter by library (permission context, optional)
        include_deleted: Include soft-deleted books (default False, RULE-012)
        skip: Pagination offset
        limit: Pagination page size (1-100)

    Returns:
        Paginated list of books

    Raises:
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Listing books: bookshelf_id={bookshelf_id}, include_deleted={include_deleted}")
        request = ListBooksRequest(
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted
        )
        use_case = di.get_list_books_use_case()
        response = await use_case.execute(request)
        logger.debug("Listed books response built successfully")
        return _serialize_response(response)
    except DomainException as error:
        logger.warning("List books failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error listing books: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list books"},
        )


# ============================================================================
# Get Book (RULE-009: Query any book)
# ============================================================================

@router.get(
    "/{book_id}",
    response_model=dict,
    summary="Get book by ID",
    description="Retrieve detailed information about a specific book"
)
async def get_book(
    book_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取书籍详情

    Args:
        book_id: Book ID to retrieve

    Returns:
        Detailed book information

    Raises:
        HTTPException 404: Book not found
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Getting book: book_id={book_id}")
        request = GetBookRequest(book_id=book_id)
        use_case = di.get_get_book_use_case()
        book = await use_case.execute(request)
        logger.debug("Retrieved book: %s", getattr(book, "id", None))
        return await _serialize_book_with_theme(book, di)
    except BookNotFoundError as error:
        logger.warning("Book not found: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )
    except DomainException as error:
        logger.warning("Get book failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error getting book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to get book"},
        )


# ============================================================================
# Update Book (RULE-010: Update metadata)
# ============================================================================

@router.patch(
    "/{book_id}",
    response_model=dict,
    summary="Update a book",
    description="Update book properties (title, summary, status, etc.)"
)
async def update_book(
    book_id: UUID,
    payload: BookUpdate,
    di: DIContainer = Depends(get_di_container)
):
    try:
        logger.info("Updating book: book_id=%s", book_id)
        cover_icon_provided = "cover_icon" in payload.model_fields_set
        cover_media_provided = "cover_media_id" in payload.model_fields_set
        update_request = UpdateBookRequest(
            book_id=book_id,
            title=payload.title,
            summary=payload.summary,
            maturity=payload.maturity.value if payload.maturity else None,
            status=None,
            is_pinned=payload.is_pinned,
            due_at=_datetime_to_iso(payload.due_at),
            tag_ids=payload.tag_ids,
            cover_icon=payload.cover_icon,
            cover_icon_provided=cover_icon_provided,
            cover_media_id=payload.cover_media_id if cover_media_provided else None,
            cover_media_id_provided=cover_media_provided,
        )
        use_case = di.get_update_book_use_case()
        updated_book = await use_case.execute(update_request)

        # Auto-refresh maturity score after metadata updates that may affect scoring
        try:
            recalc_uc = di.get_recalculate_book_maturity_use_case()
            await recalc_uc.execute(RecalcReq(book_id=book_id, trigger="update_book"))
        except Exception:  # pragma: no cover - keep write path resilient
            # Non-blocking: keep update response even if recalc fails
            logger.warning("Maturity recalc after update failed for book %s", book_id)

        logger.info("Book updated successfully: book_id=%s", book_id)
        return await _serialize_book_with_theme(updated_book, di)
    except BookNotFoundError as error:
        logger.warning("Book not found for update: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )
    except (InvalidBookMaturityTransitionError, InvalidBookDataError) as error:
        logger.warning("Invalid maturity update for book %s: %s", book_id, error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "INVALID_BOOK_MATURITY_TRANSITION"),
        )
    except DomainException as error:
        logger.warning("Book update failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error updating book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to update book"},
        )


# ============================================================================
# Upload Cover (Stable books only)
# ============================================================================

@router.post(
    "/{book_id}/cover",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload custom book cover",
    description="Upload an image via Media module and set it as book cover (only Stable, non-Legacy books)",
)
async def upload_book_cover(
    book_id: UUID,
    file: UploadFile = File(..., description="封面图片 (JPEG/PNG/WEBP/GIF, ≤10MB)"),
    di: DIContainer = Depends(get_di_container),
):
    logger.info("Uploading cover for book_id=%s", book_id)
    get_use_case = di.get_get_book_use_case()
    try:
        book = await get_use_case.execute(GetReq(book_id=book_id))
    except BookNotFoundError as error:
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )

    if not _book_allows_custom_cover(book):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "BOOK_NOT_STABLE",
                "message": "只有 Stable 阶段（且未标记 Legacy）的书籍才能上传封面图",
            },
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "封面文件不能为空"},
        )

    try:
        mime_type = _resolve_media_mime(file)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_IMAGE", "message": "仅支持 JPEG/PNG/WEBP/GIF 封面"},
        )

    filename = _normalize_filename(file.filename, mime_type)
    file_size = len(file_bytes)

    try:
        storage_key = await _book_cover_storage.save_book_cover(file_bytes, book_id, filename)
    except Exception as exc:
        logger.exception("Failed to persist book cover asset for %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "COVER_STORAGE_FAILED", "message": "无法保存封面文件"},
        ) from exc

    upload_use_case = di.get_upload_image_use_case()
    try:
        media = await upload_use_case.execute(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            user_id=None,
        )
    except (InvalidMimeTypeError, FileSizeTooLargeError, InvalidDimensionsError) as exc:
        await _book_cover_storage.delete_file(storage_key)
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    except StorageQuotaExceededError as exc:
        await _book_cover_storage.delete_file(storage_key)
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    except MediaOperationError as exc:
        await _book_cover_storage.delete_file(storage_key)
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    except Exception as exc:
        await _book_cover_storage.delete_file(storage_key)
        logger.exception("Unexpected failure uploading cover media for book %s", book_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MEDIA_UPLOAD_FAILED", "message": "封面上传失败"},
        ) from exc

    update_use_case = di.get_update_book_use_case()
    update_request = UpdateBookRequest(
        book_id=book_id,
        cover_media_id=getattr(media, "id", None),
        cover_media_id_provided=True,
    )

    try:
        updated_book = await update_use_case.execute(update_request)
    except (InvalidBookMaturityTransitionError, InvalidBookDataError) as error:
        logger.warning("Book cover assignment failed for %s: %s", book_id, error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "INVALID_BOOK_COVER_STATE"),
        )
    except DomainException as error:
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )

    return await _serialize_book_with_theme(updated_book, di)


# ============================================================================
# Delete Book (RULE-012: Soft-delete to Basement)
# ============================================================================

@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book (soft delete)",
    description="Delete book by moving to Basement (RULE-012: Soft-delete, not hard delete)"
)
async def delete_book(
    book_id: UUID,
    basement_bookshelf_id: UUID = Query(..., description="Basement bookshelf ID for soft delete"),
    di: DIContainer = Depends(get_di_container)
):
    """删除书籍（逻辑删除�?
    RULE-012: Deletion is implemented as soft-delete by moving to Basement.
    The book is not removed from database, only marked as deleted via soft_deleted_at.

    Args:
        book_id: Book ID to delete
        basement_bookshelf_id: ID of the Basement bookshelf (special container for deleted books)

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Book not found
        HTTPException 409: Book already deleted
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Soft-deleting book: book_id={book_id} to basement_id={basement_bookshelf_id}")
        request = DeleteBookRequest(
            book_id=book_id,
            basement_bookshelf_id=basement_bookshelf_id
        )
        use_case = di.get_delete_book_use_case()
        await use_case.execute(request)
        logger.info(f"Book soft-deleted successfully: book_id={book_id}")
    except BookNotFoundError as error:
        logger.warning("Book not found for deletion: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )
    except DomainException as error:
        logger.warning("Book deletion failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error deleting book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to delete book"},
        )


# ============================================================================
# Move Book (RULE-011: Transfer across bookshelves)
# ============================================================================

@router.put(
    "/{book_id}/move",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Move book to different bookshelf",
    description="Transfer a book to another bookshelf (RULE-011: Cross-bookshelf transfer)"
)
async def move_book(
    book_id: UUID,
    request: MoveBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    """移动书籍到另一个书�?(RULE-011)

    RULE-011: Books can move across bookshelves with proper authorization.
    This operation changes the book's bookshelf_id to the target bookshelf.

    Args:
        book_id: Book ID to move
        request: MoveBookRequest with:
            - target_bookshelf_id: UUID (destination bookshelf)
            - reason: Optional[str] (audit trail reason)

    Returns:
        Updated book response with new bookshelf_id

    Raises:
        HTTPException 404: Book or target bookshelf not found
        HTTPException 422: Invalid move (already in target, no permission, etc.)
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Moving book: book_id={book_id} to bookshelf={request.target_bookshelf_id}")
        request.book_id = book_id
        use_case = di.get_move_book_use_case()
        updated_book = await use_case.execute(request)
        logger.info(
            "Book moved successfully: book_id=%s to %s",
            book_id,
            request.target_bookshelf_id,
        )
        return await _serialize_book_with_theme(updated_book, di)
    except BookNotFoundError as error:
        logger.warning("Book not found for move: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )
    except InvalidBookMoveError as error:
        logger.warning("Book move validation failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "INVALID_MOVE"),
        )
    except DomainException as error:
        logger.warning("Book move failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error moving book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to move book"},
        )


# ============================================================================
# Restore Book (RULE-013: Restore from Basement)
# ============================================================================

@router.post(
    "/{book_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore a deleted book from Basement",
    description="Restore a soft-deleted book from Basement to target bookshelf (RULE-013)"
)
async def restore_book(
    book_id: UUID,
    request: RestoreBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    """恢复已删除的书籍 (RULE-013)

    RULE-013: Books can be restored from Basement to any accessible bookshelf.
    The book's soft_deleted_at flag is cleared and bookshelf_id is updated.

    Args:
        book_id: Book ID to restore
        request: RestoreBookRequest with:
            - target_bookshelf_id: UUID (destination bookshelf)

    Returns:
        Restored book response

    Raises:
        HTTPException 404: Book not found
        HTTPException 422: Book not in Basement, or target invalid
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Restoring book from Basement: book_id={book_id} to bookshelf={request.target_bookshelf_id}")
        request.book_id = book_id
        use_case = di.get_restore_book_use_case()
        restored_book = await use_case.execute(request)
        logger.info("Book restored successfully: book_id=%s", book_id)
        return await _serialize_book_with_theme(restored_book, di)
    except BookNotFoundError as error:
        logger.warning("Book not found for restore: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_404_NOT_FOUND),
            detail=_domain_error_payload(error, "BOOK_NOT_FOUND"),
        )
    except BookNotInBasementError as error:
        logger.warning("Book not in Basement: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "NOT_IN_BASEMENT"),
        )
    except InvalidBookMoveError as error:
        logger.warning("Restore validation failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "INVALID_RESTORE"),
        )
    except DomainException as error:
        logger.warning("Book restore failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error restoring book: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to restore book"},
        )


# ============================================================================
# List Deleted Books (RULE-012: Basement view)
# ============================================================================

@router.get(
    "/deleted",
    response_model=dict,
    summary="List deleted books (Basement view)",
    description="Retrieve paginated list of soft-deleted books grouped by bookshelf (RULE-012: Basement)"
)
async def list_deleted_books(
    bookshelf_id: Optional[UUID] = Query(None, description="Filter by original bookshelf_id"),
    library_id: Optional[UUID] = Query(None, description="Filter by library_id (permission context)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    di: DIContainer = Depends(get_di_container)
):
    """列出已删除的书籍 (RULE-012: Basement 视图)

    RULE-012: Shows all soft-deleted books grouped by their original bookshelf.
    This is the Basement view - a virtual container for recovery and audit purposes.

    Args:
        bookshelf_id: Filter by original bookshelf (optional)
        library_id: Filter by library (permission context, optional)
        skip: Pagination offset
        limit: Pagination page size (1-100)

    Returns:
        Paginated list of soft-deleted books, grouped by bookshelf

    Raises:
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.debug(f"Listing deleted books (Basement): bookshelf_id={bookshelf_id}")
        request = ListDeletedBooksRequest(
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_deleted_books_use_case()
        response = await use_case.execute(request)
        logger.debug("Listed deleted books from Basement")
        return _serialize_response(response)
    except DomainException as error:
        logger.warning("List deleted books failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error listing deleted books: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list deleted books"},
        )


__all__ = ["router"]


# ============================================================================
# Maturity: Recalculate (on-demand) - enables UI to refresh score and apply ops bonus
# ============================================================================

@router.post(
    "/{book_id}/maturity/recalculate",
    response_model=dict,
    summary="Recalculate maturity score for a book",
    description=(
        "Recalculate maturity_score using current snapshots. "
        "Optionally accepts operations_bonus (0-60) and other snapshot overrides."
    ),
)
async def recalculate_book_maturity(
    book_id: UUID,
    payload: dict = Body(default={}),
    di: DIContainer = Depends(get_di_container),
):
    try:
        # Build request with optional overrides; missing values fall back to snapshots
        req = RecalcReq(
            book_id=book_id,
            tag_count=payload.get("tag_count"),
            block_type_count=payload.get("block_type_count"),
            block_count=payload.get("block_count"),
            open_todo_count=payload.get("open_todo_count"),
            operations_bonus=payload.get("operations_bonus"),
            cover_icon=payload.get("cover_icon"),
            trigger=str(payload.get("trigger") or "recalculate"),
        )

        use_case = di.get_recalculate_book_maturity_use_case()
        await use_case.execute(req)

        # Fetch updated book for a consistent response shape (same as GET /books/{id})
        get_use_case = di.get_get_book_use_case()
        book = await get_use_case.execute(GetReq(book_id=book_id))
        return await _serialize_book_with_theme(book, di)

    except DomainException as error:
        logger.warning("Recalculate maturity failed: %s", error)
        raise HTTPException(
            status_code=_http_status(error, status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=_domain_error_payload(error, "VALIDATION_ERROR"),
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.error("Unexpected error recalculating maturity: %s", error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to recalculate maturity"},
        )

