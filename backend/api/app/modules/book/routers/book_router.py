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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID
import logging

from api.app.dependencies import DIContainer, get_di_container_provider
from api.app.modules.book.application.ports.input import (
    CreateBookRequest,
    ListBooksRequest,
    GetBookRequest,
    UpdateBookRequest,
    DeleteBookRequest,
    RestoreBookRequest,
    ListDeletedBooksRequest,
    MoveBookRequest,
    BookResponse,
    BookListResponse,
)
from api.app.modules.book.domain.exceptions import (
    BookNotFoundError,
    BookAlreadyExistsError,
    DomainException,
    InvalidBookMoveError,
    BookNotInBasementError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


async def get_di_container() -> DIContainer:
    """获取 DI 容器"""
    return get_di_container_provider()


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
    """创建新书�?
    Args:
        request: CreateBookRequest with:
            - bookshelf_id: UUID (required, RULE-010)
            - library_id: UUID (required, for permission check)
            - title: str (required, RULE-009 validation)
            - summary: Optional[str]

    Returns:
        Created Book response with all metadata

    Raises:
        HTTPException 409: Book already exists (duplicate check)
        HTTPException 422: Validation error (title/bookshelf invalid)
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Creating book: title='{request.title}' in bookshelf_id={request.bookshelf_id}")
        use_case = di.get_create_book_use_case()
        response: BookResponse = await use_case.execute(request)
        logger.info(f"Book created successfully: book_id={response.id}")
        return response.to_dict()
    except BookAlreadyExistsError as e:
        logger.warning(f"Book creation failed - already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "BOOK_ALREADY_EXISTS", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Book creation failed - validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error creating book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to create book"}
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
        response: BookListResponse = await use_case.execute(request)
        logger.debug(f"Listed {len(response.items)} books")
        return response.to_dict()
    except DomainException as e:
        logger.warning(f"List books failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error listing books: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list books"}
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
        response: BookResponse = await use_case.execute(request)
        logger.debug(f"Retrieved book: {response.id}")
        return response.to_dict()
    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Get book failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to get book"}
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
    request: UpdateBookRequest,
    di: DIContainer = Depends(get_di_container)
):
    """更新书籍

    Args:
        book_id: Book ID to update
        request: UpdateBookRequest with fields to update:
            - title: Optional[str]
            - summary: Optional[str]
            - status: Optional[BookStatus]
            - is_pinned: Optional[bool]
            - due_at: Optional[datetime]

    Returns:
        Updated book response

    Raises:
        HTTPException 404: Book not found
        HTTPException 422: Validation error
        HTTPException 500: Operation error
    """
    try:
        logger.info(f"Updating book: book_id={book_id}")
        request.book_id = book_id
        use_case = di.get_update_book_use_case()
        response: BookResponse = await use_case.execute(request)
        logger.info(f"Book updated successfully: book_id={book_id}")
        return response.to_dict()
    except BookNotFoundError as e:
        logger.warning(f"Book not found for update: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Book update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error updating book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to update book"}
        )


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
    except BookNotFoundError as e:
        logger.warning(f"Book not found for deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Book deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to delete book"}
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
        response: BookResponse = await use_case.execute(request)
        logger.info(f"Book moved successfully: book_id={book_id} to {request.target_bookshelf_id}")
        return response.to_dict()
    except BookNotFoundError as e:
        logger.warning(f"Book not found for move: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": str(e)}
        )
    except InvalidBookMoveError as e:
        logger.warning(f"Book move validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_MOVE", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Book move failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error moving book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to move book"}
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
        response: BookResponse = await use_case.execute(request)
        logger.info(f"Book restored successfully: book_id={book_id}")
        return response.to_dict()
    except BookNotFoundError as e:
        logger.warning(f"Book not found for restore: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOOK_NOT_FOUND", "message": str(e)}
        )
    except BookNotInBasementError as e:
        logger.warning(f"Book not in Basement: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "NOT_IN_BASEMENT", "message": str(e)}
        )
    except InvalidBookMoveError as e:
        logger.warning(f"Restore validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_RESTORE", "message": str(e)}
        )
    except DomainException as e:
        logger.warning(f"Book restore failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error restoring book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to restore book"}
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
        response: BookListResponse = await use_case.execute(request)
        logger.debug(f"Listed {len(response.items)} deleted books from Basement")
        return response.to_dict()
    except DomainException as e:
        logger.warning(f"List deleted books failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error listing deleted books: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "OPERATION_ERROR", "message": "Failed to list deleted books"}
        )


__all__ = ["router"]

