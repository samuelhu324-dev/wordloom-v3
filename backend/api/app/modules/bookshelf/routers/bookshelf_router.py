"""
Bookshelf Router - Hexagonal Architecture Pattern

书架管理的 FastAPI 路由适配器。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging
import time

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    ListBookshelvesRequest,
    GetBookshelfRequest,
    UpdateBookshelfRequest,
    DeleteBookshelfRequest,
    GetBasementRequest,
    BookshelfDashboardRequest,
    BookshelfDashboardSort,
    BookshelfDashboardFilter,
    BookshelfResponse,
)
from api.app.modules.bookshelf.exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
    BookshelfPersistenceError,
    DomainException,
)
from api.app.modules.bookshelf.schemas import BookshelfDashboardResponse

from api.app.config.security import get_current_actor
from api.app.shared.actor import Actor
from api.app.config.setting import get_settings


logger = logging.getLogger(__name__)

_settings = get_settings()

router = APIRouter(prefix="", tags=["bookshelves"])

# Re-export get_di_container for use with Depends()
# This is the proper async dependency that FastAPI will handle
# FastAPI will automatically inject the result of this function as the 'di' parameter


# ============================================================================
# Create Bookshelf
# ============================================================================

@router.post(
    "",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bookshelf",
)
async def create_bookshelf(
    request: CreateBookshelfRequest,
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """创建新书架"""
    start_time = time.time()
    logger.info(f"[CREATE_BOOKSHELF] START - library_id={request.library_id}, name={request.name}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        request = request.model_copy(
            update={
                "actor_user_id": actor.user_id,
                "enforce_owner_check": enforce_owner_check,
            }
        )
        use_case = di.get_create_bookshelf_use_case()
        result = await use_case.execute(request)
        elapsed = time.time() - start_time
        logger.info(f"[CREATE_BOOKSHELF] SUCCESS - id={result.id}, elapsed={elapsed:.3f}s")
        return {
            "id": str(result.id),
            "library_id": str(result.library_id),
            "name": result.name,
            "description": result.description,
            "is_pinned": result.is_pinned,
            "is_favorite": result.is_favorite,
            "is_basement": result.is_basement,
            "status": result.status,
            "created_at": result.created_at,
            "updated_at": result.created_at,
            "tags_summary": result.tags_summary,
            "tags": result.tags_summary,
            "tag_ids": [str(tag_id) for tag_id in result.tag_ids],
        }
    except BookshelfAlreadyExistsError as e:
        elapsed = time.time() - start_time
        logger.warning(f"[CREATE_BOOKSHELF] CONFLICT - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[CREATE_BOOKSHELF] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )
    except Exception as e:
        elapsed = time.time() - start_time
        # Expanded diagnostics for temporary debugging of 500 errors
        logger.error(
            f"[CREATE_BOOKSHELF] ERROR - {type(e).__name__}: {e}; payload library_id={request.library_id} name={request.name}, elapsed={elapsed:.3f}s",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# ============================================================================
# Dashboard Overview
# ============================================================================


@router.get(
    "/dashboard",
    response_model=BookshelfDashboardResponse,
    summary="Get bookshelf dashboard overview",
)
async def get_bookshelf_dashboard(
    library_id: UUID = Query(..., description="Library ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: BookshelfDashboardSort = Query(BookshelfDashboardSort.RECENT_ACTIVITY),
    status_filter: BookshelfDashboardFilter = Query(BookshelfDashboardFilter.ACTIVE),
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container),
):
    """获取书架运营面板数据"""

    enforce_owner_check = not _settings.allow_dev_library_owner_override
    request = BookshelfDashboardRequest(
        library_id=library_id,
        actor_user_id=actor.user_id,
        enforce_owner_check=enforce_owner_check,
        page=page,
        size=size,
        sort=sort,
        status_filter=status_filter,
    )

    try:
        use_case = di.get_bookshelf_dashboard_use_case()
        result = await use_case.execute(request)
    except DomainException as e:
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )

    items = [
        {
            "id": item.id,
            "library_id": item.library_id,
            "name": item.name,
            "description": item.description,
            "status": item.status,
            "is_pinned": item.is_pinned,
            "is_archived": item.is_archived,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "last_activity_at": item.last_activity_at,
            "health": item.health,
            "theme_color": item.theme_color,
            "cover_media_id": item.cover_media_id,
            "tag_ids": [str(tag_id) for tag_id in item.tag_ids],
            "tags_summary": item.tag_names,
            "tags": [
                {
                    "id": str(tag.id),
                    "name": tag.name,
                    "color": tag.color,
                    "description": tag.description,
                }
                for tag in item.tags
            ],
            "book_counts": {
                "total": item.book_counts.total,
                "seed": item.book_counts.seed,
                "growing": item.book_counts.growing,
                "stable": item.book_counts.stable,
                "legacy": item.book_counts.legacy,
            },
            "edits_last_7d": item.edits_last_7d,
            "views_last_7d": item.views_last_7d,
        }
        for item in result.items
    ]

    snapshot = {
        "total": result.snapshot.total,
        "pinned": result.snapshot.pinned,
        "health": {
            "active": result.snapshot.health_counts.active,
            "slowing": result.snapshot.health_counts.slowing,
            "cooling": result.snapshot.health_counts.cooling,
            "archived": result.snapshot.health_counts.archived,
        },
    }

    return BookshelfDashboardResponse(
        total=result.total,
        page=page,
        page_size=size,
        items=items,
        snapshot=snapshot,
    )


# ============================================================================
# List Bookshelves
# ============================================================================

@router.get(
    "",
    response_model=None,
    summary="List all bookshelves",
)
async def list_bookshelves(
    library_id: UUID = Query(..., description="Library ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """列出所有书架"""
    start_time = time.time()
    logger.info(f"[LIST_BOOKSHELVES] START - library_id={library_id}, skip={skip}, limit={limit}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        request = ListBookshelvesRequest(
            library_id=library_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=enforce_owner_check,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_bookshelves_use_case()
        bookshelves = await use_case.execute(request)
        elapsed = time.time() - start_time
        logger.info(f"[LIST_BOOKSHELVES] SUCCESS - count={len(bookshelves)}, elapsed={elapsed:.3f}s")
        return {
            "total": len(bookshelves),
            "items": [
                {
                    "id": str(r.id),
                    "library_id": str(r.library_id),
                    "name": str(r.name),  # Safe: convert to str
                    "description": str(r.description) if r.description else None,
                    "is_pinned": r.is_pinned,
                    "is_favorite": r.is_favorite,
                    "is_basement": r.type.value == "basement",
                    "status": r.status.value,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in bookshelves
            ]
        }
    except BookshelfPersistenceError as e:
        elapsed = time.time() - start_time
        logger.error(f"[LIST_BOOKSHELVES] PERSISTENCE_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[LIST_BOOKSHELVES] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"[LIST_BOOKSHELVES] ERROR - {type(e).__name__}: {e}; library_id={library_id} skip={skip} limit={limit}, elapsed={elapsed:.3f}s",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# ============================================================================
# Get Bookshelf
# ============================================================================

@router.get(
    "/{bookshelf_id}",
    response_model=None,
    summary="Get bookshelf by ID",
)
async def get_bookshelf(
    bookshelf_id: UUID,
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """获取书架详情"""
    start_time = time.time()
    logger.info(f"[GET_BOOKSHELF] START - bookshelf_id={bookshelf_id}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        request = GetBookshelfRequest(
            bookshelf_id=bookshelf_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=enforce_owner_check,
        )
        use_case = di.get_get_bookshelf_use_case()
        response = await use_case.execute(request)  # Returns GetBookshelfResponse DTO
        elapsed = time.time() - start_time
        logger.info(f"[GET_BOOKSHELF] SUCCESS - id={response.id}, elapsed={elapsed:.3f}s")
        # Adapt to unified JSON shape used by other endpoints
        return {
            "id": str(response.id),
            "library_id": str(response.library_id),
            "name": response.name,
            "description": response.description,
            "is_pinned": response.is_pinned,
            "is_favorite": response.is_favorite,
            "is_basement": response.bookshelf_type == "basement",
            "status": response.status,
            "created_at": response.created_at or None,
            "updated_at": response.updated_at or None,
        }
    except BookshelfNotFoundError as e:
        elapsed = time.time() - start_time
        logger.warning(f"[GET_BOOKSHELF] NOT_FOUND - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[GET_BOOKSHELF] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[GET_BOOKSHELF] ERROR - {type(e).__name__}: {str(e)}, elapsed={elapsed:.3f}s", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Update Bookshelf
# ============================================================================

@router.patch(
    "/{bookshelf_id}",
    response_model=None,
    summary="Update a bookshelf",
)
async def update_bookshelf(
    bookshelf_id: UUID,
    request: UpdateBookshelfRequest,
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """更新书架"""
    start_time = time.time()
    logger.info(f"[UPDATE_BOOKSHELF] START - bookshelf_id={bookshelf_id}, name={request.name}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        payload = request.model_copy(
            update={
                "bookshelf_id": bookshelf_id,
                "actor_user_id": actor.user_id,
                "enforce_owner_check": enforce_owner_check,
            }
        )
        use_case = di.get_update_bookshelf_use_case()
        result = await use_case.execute(payload)
        elapsed = time.time() - start_time
        logger.info(f"[UPDATE_BOOKSHELF] SUCCESS - id={result.id}, elapsed={elapsed:.3f}s")
        return {
            "id": str(result.id),
            "library_id": str(result.library_id),
            "name": result.name,
            "description": result.description,
            "is_pinned": result.is_pinned,
            "is_favorite": result.is_favorite,
            "is_basement": result.is_basement,
            "status": result.status,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "tags_summary": result.tags_summary,
            "tags": result.tags_summary,
            "tag_ids": [str(tag_id) for tag_id in result.tag_ids],
        }
    except BookshelfNotFoundError as e:
        elapsed = time.time() - start_time
        logger.warning(f"[UPDATE_BOOKSHELF] NOT_FOUND - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[UPDATE_BOOKSHELF] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=e.http_status_code if hasattr(e, "http_status_code") else status.HTTP_400_BAD_REQUEST,
            detail=getattr(e, "to_dict", lambda: str(e))()
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[UPDATE_BOOKSHELF] ERROR - {type(e).__name__}: {str(e)}, elapsed={elapsed:.3f}s", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Delete Bookshelf
# ============================================================================

@router.delete(
    "/{bookshelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bookshelf",
)
async def delete_bookshelf(
    bookshelf_id: UUID,
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """删除书架"""
    start_time = time.time()
    logger.info(f"[DELETE_BOOKSHELF] START - bookshelf_id={bookshelf_id}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        request = DeleteBookshelfRequest(
            bookshelf_id=bookshelf_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=enforce_owner_check,
        )
        use_case = di.get_delete_bookshelf_use_case()
        await use_case.execute(request)
        elapsed = time.time() - start_time
        logger.info(f"[DELETE_BOOKSHELF] SUCCESS - elapsed={elapsed:.3f}s")
    except BookshelfNotFoundError as e:
        elapsed = time.time() - start_time
        logger.warning(f"[DELETE_BOOKSHELF] NOT_FOUND - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[DELETE_BOOKSHELF] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[DELETE_BOOKSHELF] ERROR - {type(e).__name__}: {str(e)}, elapsed={elapsed:.3f}s", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Get Basement (Special Bookshelf)
# ============================================================================

@router.get(
    "/basement",
    response_model=None,
    summary="Get the Basement bookshelf",
)
async def get_basement(
    library_id: UUID = Query(..., description="Library ID"),
    actor: Actor = Depends(get_current_actor),
    di: DIContainer = Depends(get_di_container)
):
    """获取 Basement（特殊书架）"""
    start_time = time.time()
    logger.info(f"[GET_BASEMENT] START - library_id={library_id}")
    try:
        enforce_owner_check = not _settings.allow_dev_library_owner_override
        request = GetBasementRequest(
            library_id=library_id,
            actor_user_id=actor.user_id,
            enforce_owner_check=enforce_owner_check,
        )
        use_case = di.get_get_basement_use_case()
        bookshelf = await use_case.execute(request)
        elapsed = time.time() - start_time
        logger.info(f"[GET_BASEMENT] SUCCESS - id={bookshelf.id}, elapsed={elapsed:.3f}s")
        return {
            "id": str(bookshelf.id),
            "library_id": str(bookshelf.library_id),
            "name": str(bookshelf.name),  # Safe: convert to str
            "description": str(bookshelf.description) if bookshelf.description else None,
            "is_pinned": bookshelf.is_pinned,
            "is_favorite": bookshelf.is_favorite,
            "is_basement": bookshelf.type.value == "basement",
            "status": bookshelf.status.value,
            "created_at": bookshelf.created_at.isoformat() if bookshelf.created_at else None,
        }
    except BookshelfNotFoundError as e:
        elapsed = time.time() - start_time
        logger.warning(f"[GET_BASEMENT] NOT_FOUND - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        elapsed = time.time() - start_time
        logger.warning(f"[GET_BASEMENT] DOMAIN_ERROR - {str(e)}, elapsed={elapsed:.3f}s")
        raise HTTPException(
            status_code=getattr(e, "http_status_code", getattr(e, "http_status", status.HTTP_400_BAD_REQUEST)),
            detail=getattr(e, "to_dict", lambda: str(e))(),
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[GET_BASEMENT] ERROR - {type(e).__name__}: {str(e)}, elapsed={elapsed:.3f}s", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


__all__ = ["router"]


