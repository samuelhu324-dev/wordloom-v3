"""
Bookshelf Router - Hexagonal Architecture Pattern

书架管理的 FastAPI 路由适配器。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    ListBookshelvesRequest,
    GetBookshelfRequest,
    UpdateBookshelfRequest,
    DeleteBookshelfRequest,
    GetBasementRequest,
    BookshelfResponse,
)
from app.modules.bookshelf.domain.exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookshelves", tags=["bookshelves"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


# ============================================================================
# Create Bookshelf
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bookshelf",
)
async def create_bookshelf(
    request: CreateBookshelfRequest,
    di: DIContainer = Depends(get_di_container)
):
    """创建新书架"""
    try:
        use_case = di.get_create_bookshelf_use_case()
        response: BookshelfResponse = await use_case.execute(request)
        return response.to_dict()
    except BookshelfAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# List Bookshelves
# ============================================================================

@router.get(
    "",
    response_model=dict,
    summary="List all bookshelves",
)
async def list_bookshelves(
    library_id: UUID = Query(..., description="Library ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    di: DIContainer = Depends(get_di_container)
):
    """列出所有书架"""
    try:
        request = ListBookshelvesRequest(
            library_id=library_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_bookshelves_use_case()
        responses: List[BookshelfResponse] = await use_case.execute(request)
        return {
            "total": len(responses),
            "items": [r.to_dict() for r in responses]
        }
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Get Bookshelf
# ============================================================================

@router.get(
    "/{bookshelf_id}",
    response_model=dict,
    summary="Get bookshelf by ID",
)
async def get_bookshelf(
    bookshelf_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取书架详情"""
    try:
        request = GetBookshelfRequest(bookshelf_id=bookshelf_id)
        use_case = di.get_get_bookshelf_use_case()
        response: BookshelfResponse = await use_case.execute(request)
        return response.to_dict()
    except BookshelfNotFoundError as e:
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
# Update Bookshelf
# ============================================================================

@router.patch(
    "/{bookshelf_id}",
    response_model=dict,
    summary="Update a bookshelf",
)
async def update_bookshelf(
    bookshelf_id: UUID,
    request: UpdateBookshelfRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新书架"""
    try:
        request.bookshelf_id = bookshelf_id
        use_case = di.get_update_bookshelf_use_case()
        response: BookshelfResponse = await use_case.execute(request)
        return response.to_dict()
    except BookshelfNotFoundError as e:
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
# Delete Bookshelf
# ============================================================================

@router.delete(
    "/{bookshelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bookshelf",
)
async def delete_bookshelf(
    bookshelf_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除书架"""
    try:
        request = DeleteBookshelfRequest(bookshelf_id=bookshelf_id)
        use_case = di.get_delete_bookshelf_use_case()
        await use_case.execute(request)
    except BookshelfNotFoundError as e:
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
# Get Basement (Special Bookshelf)
# ============================================================================

@router.get(
    "/basement",
    response_model=dict,
    summary="Get the Basement bookshelf",
)
async def get_basement(
    library_id: UUID = Query(..., description="Library ID"),
    di: DIContainer = Depends(get_di_container)
):
    """获取 Basement（特殊书架）"""
    try:
        request = GetBasementRequest(library_id=library_id)
        use_case = di.get_get_basement_use_case()
        response: BookshelfResponse = await use_case.execute(request)
        return response.to_dict()
    except BookshelfNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
