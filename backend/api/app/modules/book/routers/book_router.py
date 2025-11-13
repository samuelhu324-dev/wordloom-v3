"""
Book Router - Hexagonal Architecture Pattern

书籍管理的 FastAPI 路由适配器。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import logging

from dependencies import DIContainer, get_di_container_provider
from app.modules.book.application.ports.input import (
    CreateBookRequest,
    ListBooksRequest,
    GetBookRequest,
    UpdateBookRequest,
    DeleteBookRequest,
    RestoreBookRequest,
    ListDeletedBooksRequest,
    BookResponse,
    BookListResponse,
)
from app.modules.book.domain.exceptions import (
    BookNotFoundError,
    BookAlreadyExistsError,
    DomainException,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


# ============================================================================
# Create Book
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
)
async def create_book(
    request: CreateBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    """创建新书籍"""
    try:
        use_case = di.get_create_book_use_case()
        response: BookResponse = await use_case.execute(request)
        return response.to_dict()
    except BookAlreadyExistsError as e:
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
# List Books
# ============================================================================

@router.get(
    "",
    response_model=dict,
    summary="List books",
)
async def list_books(
    bookshelf_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    di: DIContainer = Depends(get_di_container)
):
    """列出书籍"""
    try:
        request = ListBooksRequest(
            bookshelf_id=bookshelf_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_books_use_case()
        response: BookListResponse = await use_case.execute(request)
        return response.to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Get Book
# ============================================================================

@router.get(
    "/{book_id}",
    response_model=dict,
    summary="Get book by ID",
)
async def get_book(
    book_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """获取书籍详情"""
    try:
        request = GetBookRequest(book_id=book_id)
        use_case = di.get_get_book_use_case()
        response: BookResponse = await use_case.execute(request)
        return response.to_dict()
    except BookNotFoundError as e:
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
# Update Book
# ============================================================================

@router.patch(
    "/{book_id}",
    response_model=dict,
    summary="Update a book",
)
async def update_book(
    book_id: UUID,
    request: UpdateBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新书籍"""
    try:
        request.book_id = book_id
        use_case = di.get_update_book_use_case()
        response: BookResponse = await use_case.execute(request)
        return response.to_dict()
    except BookNotFoundError as e:
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
# Delete Book
# ============================================================================

@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book (soft delete)",
)
async def delete_book(
    book_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """删除书籍（逻辑删除）"""
    try:
        request = DeleteBookRequest(book_id=book_id)
        use_case = di.get_delete_book_use_case()
        await use_case.execute(request)
    except BookNotFoundError as e:
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
# Restore Book
# ============================================================================

@router.post(
    "/{book_id}/restore",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Restore a deleted book",
)
async def restore_book(
    book_id: UUID,
    di: DIContainer = Depends(get_di_container)
):
    """恢复已删除的书籍"""
    try:
        request = RestoreBookRequest(book_id=book_id)
        use_case = di.get_restore_book_use_case()
        response: BookResponse = await use_case.execute(request)
        return response.to_dict()
    except BookNotFoundError as e:
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
# List Deleted Books
# ============================================================================

@router.get(
    "/deleted",
    response_model=dict,
    summary="List deleted books",
)
async def list_deleted_books(
    bookshelf_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    di: DIContainer = Depends(get_di_container)
):
    """列出已删除的书籍"""
    try:
        request = ListDeletedBooksRequest(
            bookshelf_id=bookshelf_id,
            skip=skip,
            limit=limit
        )
        use_case = di.get_list_deleted_books_use_case()
        response: BookListResponse = await use_case.execute(request)
        return response.to_dict()
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


__all__ = ["router"]
