"""
Bookshelf Router - FastAPI 路由

完整的 API 端点实现，支持：
  - RULE-004: 无限创建 Bookshelf
  - RULE-005: Library 关联检查
  - RULE-006: 名称唯一性检查
  - RULE-010: Basement 特殊处理

体系结构：
  ├─ Dependency Injection (获取 Service)
  ├─ Request Validation (Pydantic schemas)
  ├─ Business Logic Execution (Service 层)
  ├─ Exception Handling (Domain exceptions → HTTP)
  ├─ Response Serialization (Schemas)
  └─ Logging & Monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
import logging

from modules.bookshelf.schemas import (
    BookshelfCreate,
    BookshelfUpdate,
    BookshelfResponse,
    BookshelfDetailResponse,
    BookshelfPaginatedResponse,
    ErrorDetail,
)
from modules.bookshelf.service import BookshelfService
from modules.bookshelf.repository import BookshelfRepositoryImpl
from modules.bookshelf.exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
    InvalidBookshelfNameError,
    BasementOperationError,
    BookshelfLibraryAssociationError,
    BookshelfException,
)
from infra.database import get_db_session
from core.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/libraries/{library_id}/bookshelves",
    tags=["bookshelves"],
    responses={
        404: {"description": "Bookshelf or Library not found", "model": ErrorDetail},
        409: {"description": "Conflict (e.g., duplicate name)", "model": ErrorDetail},
        422: {"description": "Validation error", "model": ErrorDetail},
    },
)


# ============================================
# Dependency Injection
# ============================================

async def get_bookshelf_service(
    session: AsyncSession = Depends(get_db_session),
) -> BookshelfService:
    """
    依赖注入：获取 BookshelfService

    DDD 分层链：
      1. Session (Database connection)
      2. Repository (Data access layer)
      3. Service (Business logic layer)
    """
    repository = BookshelfRepositoryImpl(session)
    service = BookshelfService(repository)
    logger.debug(f"BookshelfService initialized with session {id(session)}")
    return service


# ============================================
# Exception Handlers
# ============================================

def _handle_domain_exception(exc: BookshelfException) -> HTTPException:
    """将 Domain Exception 映射到 HTTP Exception"""
    error_detail = exc.to_dict() if hasattr(exc, "to_dict") else {"message": str(exc)}
    logger.warning(f"Domain exception: {exc.code if hasattr(exc, 'code') else 'UNKNOWN'} - {str(exc)}")

    return HTTPException(
        status_code=exc.http_status if hasattr(exc, "http_status") else 500,
        detail=error_detail,
    )


# ============================================
# Routes
# ============================================

@router.post(
    "",
    response_model=BookshelfResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Bookshelf",
    description="在指定 Library 下创建新的 Bookshelf（RULE-004 无限创建，RULE-006 名称唯一检查）",
)
async def create_bookshelf(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    request: BookshelfCreate = None,
    user_id: UUID = Depends(get_current_user_id),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Create a new Bookshelf in a Library"""
    try:
        logger.info(f"Creating Bookshelf '{request.name}' in Library {library_id} for user {user_id}")
        bookshelf = await service.create_bookshelf(
            library_id=library_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
        )
        logger.info(f"Bookshelf created successfully: {bookshelf.id}")
        return BookshelfResponse.model_validate(bookshelf)
    except BookshelfAlreadyExistsError as exc:
        logger.warning(f"Conflict: {exc.message}")
        raise _handle_domain_exception(exc)
    except InvalidBookshelfNameError as exc:
        logger.warning(f"Validation failed: {exc.message}")
        raise _handle_domain_exception(exc)
    except BookshelfException as exc:
        logger.error(f"Unexpected bookshelf exception: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.get(
    "",
    response_model=BookshelfPaginatedResponse,
    summary="List Bookshelves",
    description="获取 Library 下的所有 Bookshelf（支持分页和过滤）",
)
async def list_bookshelves(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_basement: bool = Query(False, description="是否包含 Basement"),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfPaginatedResponse:
    """List all Bookshelves in a Library"""
    try:
        logger.debug(f"Listing Bookshelves in Library {library_id} (page {page}, size {page_size})")
        result = await service.list_bookshelves(
            library_id=library_id,
            page=page,
            page_size=page_size,
            include_basement=include_basement,
        )
        logger.debug(f"Retrieved {len(result['items'])} bookshelves")
        return BookshelfPaginatedResponse(**result)
    except BookshelfException as exc:
        logger.error(f"Error listing bookshelves: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.get(
    "/{bookshelf_id}",
    response_model=BookshelfDetailResponse,
    summary="Get Bookshelf",
    description="获取指定 Bookshelf 的详细信息",
)
async def get_bookshelf(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    bookshelf_id: UUID = Path(..., description="Bookshelf 的唯一 ID"),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfDetailResponse:
    """Get a Bookshelf by ID"""
    try:
        logger.debug(f"Fetching Bookshelf {bookshelf_id}")
        bookshelf = await service.get_bookshelf(bookshelf_id, library_id)
        return BookshelfDetailResponse.model_validate(bookshelf)
    except BookshelfNotFoundError as exc:
        logger.warning(f"Not found: {exc.message}")
        raise _handle_domain_exception(exc)
    except BookshelfException as exc:
        logger.error(f"Error fetching bookshelf: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.put(
    "/{bookshelf_id}",
    response_model=BookshelfResponse,
    summary="Update Bookshelf",
    description="更新 Bookshelf 信息（RULE-010: Basement 不能修改）",
)
async def update_bookshelf(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    bookshelf_id: UUID = Path(..., description="Bookshelf 的唯一 ID"),
    request: BookshelfUpdate = None,
    user_id: UUID = Depends(get_current_user_id),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Update a Bookshelf"""
    try:
        logger.info(f"Updating Bookshelf {bookshelf_id}")
        bookshelf = await service.get_bookshelf(bookshelf_id, library_id)
        if bookshelf.library_id != library_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bookshelf belongs to a different Library",
            )
        if getattr(bookshelf, "is_basement", False) and (request.name or request.description):
            raise _handle_domain_exception(
                BasementOperationError(
                    str(bookshelf_id),
                    "update",
                    "Cannot modify Basement Bookshelf"
                )
            )
        if request.name:
            bookshelf = await service.rename_bookshelf(bookshelf_id, request.name)
        if request.is_pinned is not None:
            bookshelf = await service.set_pinned(bookshelf_id, request.is_pinned)
        if request.is_favorite is not None:
            bookshelf = await service.set_favorite(bookshelf_id, request.is_favorite)
        logger.info(f"Bookshelf {bookshelf_id} updated successfully")
        return BookshelfResponse.model_validate(bookshelf)
    except BookshelfNotFoundError as exc:
        raise _handle_domain_exception(exc)
    except (InvalidBookshelfNameError, BasementOperationError) as exc:
        raise _handle_domain_exception(exc)
    except BookshelfException as exc:
        logger.error(f"Update failed: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.delete(
    "/{bookshelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Bookshelf",
    description="删除 Bookshelf（级联转移 Books 到 Basement，RULE-010: Basement 不能删除）",
)
async def delete_bookshelf(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    bookshelf_id: UUID = Path(..., description="Bookshelf 的唯一 ID"),
    user_id: UUID = Depends(get_current_user_id),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> None:
    """Delete a Bookshelf"""
    try:
        logger.info(f"Deleting Bookshelf {bookshelf_id} for user {user_id}")
        bookshelf = await service.get_bookshelf(bookshelf_id, library_id)
        if bookshelf.library_id != library_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bookshelf belongs to a different Library",
            )
        if getattr(bookshelf, "is_basement", False):
            raise _handle_domain_exception(
                BasementOperationError(
                    str(bookshelf_id),
                    "delete",
                    "Basement Bookshelf cannot be deleted"
                )
            )
        await service.delete_bookshelf(bookshelf_id)
        logger.info(f"Bookshelf {bookshelf_id} deleted successfully")
    except BookshelfNotFoundError as exc:
        raise _handle_domain_exception(exc)
    except BasementOperationError as exc:
        raise _handle_domain_exception(exc)
    except BookshelfException as exc:
        logger.error(f"Deletion failed: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)


@router.get(
    "/basement/default",
    response_model=BookshelfDetailResponse,
    summary="Get Basement Bookshelf",
    description="获取 Library 的 Basement Bookshelf（RULE-010）",
)
async def get_basement_bookshelf(
    library_id: UUID = Path(..., description="Library 的唯一 ID"),
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfDetailResponse:
    """Get the Basement Bookshelf for a Library"""
    try:
        logger.debug(f"Fetching Basement Bookshelf for Library {library_id}")
        basement = await service.get_basement_bookshelf(library_id)
        return BookshelfDetailResponse.model_validate(basement)
    except BookshelfNotFoundError as exc:
        logger.warning(f"Basement not found: {exc.message}")
        raise _handle_domain_exception(exc)
    except BookshelfException as exc:
        logger.error(f"Error fetching basement: {exc.message}", exc_info=True)
        raise _handle_domain_exception(exc)

