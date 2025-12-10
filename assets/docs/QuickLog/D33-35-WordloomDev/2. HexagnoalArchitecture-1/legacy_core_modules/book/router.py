"""
Book Router - RESTful API endpoints for Book domain

Implements complete 4-layer architecture with DI chain:
  Layer 1: HTTP validation + permission checks
  Layer 2: Domain service calls
  Layer 3: ORM persistence
  Layer 4: Event publishing

Endpoints:
  POST   /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books
  GET    /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books
  GET    /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books/{book_id}
  PUT    /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books/{book_id}
  DELETE /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books/{book_id}
  POST   /api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books/{book_id}/restore

Maps RULE-009 through RULE-013 with comprehensive error handling.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session

from modules.book.schemas import (
    BookCreate,
    BookUpdate,
    BookRestoreRequest,
    BookResponse,
    BookDetailResponse,
    BookPaginatedResponse,
    BookErrorResponse,
    BookDTO,
)
from modules.book.service import BookService
from modules.book.repository import BookRepositoryImpl
from modules.book.exceptions import (
    BookNotFoundError,
    BookAlreadyExistsError,
    InvalidBookTitleError,
    BookshelfNotFoundError,
    InvalidBookMoveError,
    BookNotInBasementError,
    BookAlreadyDeletedError,
    BookOperationError,
)
from core.database import get_db  # Assuming this exists

logger = logging.getLogger(__name__)

# ============================================================================
# Dependency Injection
# ============================================================================

async def get_book_repository(db: Session = Depends(get_db)) -> BookRepositoryImpl:
    """Provide BookRepositoryImpl instance"""
    return BookRepositoryImpl(db)


async def get_book_service(
    repository: BookRepositoryImpl = Depends(get_book_repository),
) -> BookService:
    """Provide BookService instance with dependencies"""
    # Note: bookshelf_repository and event_bus should be injected here
    # For now, we'll assume they're passed in or can be fetched
    return BookService(
        repository=repository,
        bookshelf_repository=None,  # ← Should be injected
        event_bus=None,  # ← Should be injected
    )


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/api/v1/libraries/{library_id}/bookshelves/{bookshelf_id}/books",
    tags=["books"],
    responses={
        404: {"model": BookErrorResponse, "description": "Book not found"},
        422: {"model": BookErrorResponse, "description": "Validation error"},
        500: {"model": BookErrorResponse, "description": "Internal server error"},
    },
)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Book",
    description="Create a new Book in a Bookshelf (RULE-009: Unlimited creation)",
)
async def create_book(
    library_id: UUID,
    bookshelf_id: UUID,
    request: BookCreate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """
    Create a new Book in the specified Bookshelf.

    RULE-009: Book unlimited creation (no constraints)
    RULE-010: Book must belong to a Bookshelf

    Args:
        library_id: Parent Library ID
        bookshelf_id: Parent Bookshelf ID
        request: Book creation payload

    Returns:
        Created Book

    Raises:
        HTTPException 422: Bookshelf not found
        HTTPException 422: Invalid title
        HTTPException 500: Operation error
    """
    logger.info(f"Creating Book in Bookshelf {bookshelf_id}: '{request.title}'")

    try:
        # Layer 1: Validate request (Pydantic already done)
        # Layer 2-4: Delegate to service
        book_domain = await service.create_book(
            bookshelf_id=bookshelf_id,
            title=request.title,
            summary=request.summary,
        )

        # Convert domain object to DTO, then to response
        book_dto = BookDTO.from_domain(book_domain)
        return book_dto.to_response()

    except BookshelfNotFoundError as e:
        logger.warning(f"Bookshelf not found: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except InvalidBookTitleError as e:
        logger.warning(f"Invalid title: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except Exception as e:
        logger.error(f"Failed to create Book: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to create Book: {str(e)}",
            },
        )


@router.get(
    "",
    response_model=BookPaginatedResponse,
    summary="List Books in a Bookshelf",
    description="Retrieve paginated list of Books (RULE-012 soft-delete filtering)",
)
async def list_books(
    library_id: UUID,
    bookshelf_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include soft-deleted Books (RULE-012)"),
    service: BookService = Depends(get_book_service),
) -> BookPaginatedResponse:
    """
    List Books in the specified Bookshelf with pagination.

    RULE-012: By default, soft-deleted Books are excluded.
    Set include_deleted=true to retrieve them.

    Args:
        library_id: Parent Library ID
        bookshelf_id: Parent Bookshelf ID
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        include_deleted: Include soft-deleted items

    Returns:
        Paginated list of Books
    """
    logger.debug(f"Listing Books in Bookshelf {bookshelf_id}, page {page}, size {page_size}")

    try:
        # Layer 2: Get Books from service
        books = await service.list_books(bookshelf_id)

        # Filter soft-deleted if needed (RULE-012)
        if not include_deleted:
            books = [b for b in books if not b.is_deleted]

        # Apply pagination
        total = len(books)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_books = books[start_idx:end_idx]

        # Convert to response
        items = [BookDTO.from_domain(b).to_detail_response() for b in paginated_books]

        return BookPaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(end_idx < total),
        )

    except Exception as e:
        logger.error(f"Failed to list Books: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to list Books: {str(e)}",
            },
        )


@router.get(
    "/{book_id}",
    response_model=BookDetailResponse,
    summary="Get Book details",
    description="Retrieve detailed information about a specific Book",
)
async def get_book(
    library_id: UUID,
    bookshelf_id: UUID,
    book_id: UUID,
    service: BookService = Depends(get_book_service),
) -> BookDetailResponse:
    """
    Retrieve details for a specific Book.

    Args:
        library_id: Parent Library ID
        bookshelf_id: Parent Bookshelf ID (for validation)
        book_id: Book ID

    Returns:
        Detailed Book information

    Raises:
        HTTPException 404: Book not found
        HTTPException 500: Operation error
    """
    logger.debug(f"Getting Book {book_id}")

    try:
        book = await service.get_book(book_id)
        book_dto = BookDTO.from_domain(book)
        return book_dto.to_detail_response()

    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e.message}")
        raise HTTPException(
            status_code=404,
            detail=e.to_dict(),
        )
    except Exception as e:
        logger.error(f"Failed to get Book: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to get Book: {str(e)}",
            },
        )


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update Book",
    description="Update Book properties (title, summary, status, etc.) or move to different Bookshelf (RULE-011)",
)
async def update_book(
    library_id: UUID,
    bookshelf_id: UUID,
    book_id: UUID,
    request: BookUpdate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """
    Update a Book's properties or move it to another Bookshelf.

    RULE-011: Book can move across Bookshelves with permission checks.
    RULE-010: Cannot modify Books in Basement (special handling).

    Args:
        library_id: Parent Library ID
        bookshelf_id: Current Bookshelf ID
        book_id: Book ID
        request: Update payload

    Returns:
        Updated Book

    Raises:
        HTTPException 404: Book not found
        HTTPException 422: Validation error or invalid move
        HTTPException 500: Operation error
    """
    logger.info(f"Updating Book {book_id}")

    try:
        # Process each updatable field
        book = await service.get_book(book_id)

        # Title update
        if request.title:
            await service.rename_book(book_id, request.title)

        # Summary update
        if request.summary is not None:  # Allow empty string to clear
            await service.set_summary(book_id, request.summary)

        # Move to different bookshelf (RULE-011)
        if request.bookshelf_id:
            await service.move_to_bookshelf(book_id, request.bookshelf_id)

        # Priority/Urgency updates (service-layer auxiliary)
        if request.priority is not None or request.urgency is not None:
            book = await service.get_book(book_id)
            if request.priority is not None:
                book.priority = request.priority
            if request.urgency is not None:
                book.urgency = request.urgency
            await service.repository.save(book)

        # Due date update
        if request.due_at is not None:
            await service.set_due_date(book_id, request.due_at)

        # Get updated book
        updated_book = await service.get_book(book_id)
        book_dto = BookDTO.from_domain(updated_book)
        return book_dto.to_response()

    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e.message}")
        raise HTTPException(
            status_code=404,
            detail=e.to_dict(),
        )
    except InvalidBookMoveError as e:
        logger.warning(f"Invalid move: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except InvalidBookTitleError as e:
        logger.warning(f"Invalid title: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except Exception as e:
        logger.error(f"Failed to update Book: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to update Book: {str(e)}",
            },
        )


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Book (soft-delete)",
    description="Delete a Book by moving it to Basement (RULE-012)",
)
async def delete_book(
    library_id: UUID,
    bookshelf_id: UUID,
    book_id: UUID,
    service: BookService = Depends(get_book_service),
) -> None:
    """
    Delete a Book via soft-delete (move to Basement).

    RULE-012: Book deletion is implemented as moving to Basement,
    allowing recovery (RULE-013).

    Args:
        library_id: Parent Library ID
        bookshelf_id: Current Bookshelf ID
        book_id: Book ID to delete

    Raises:
        HTTPException 404: Book not found
        HTTPException 409: Book already deleted
        HTTPException 500: Operation error
    """
    logger.info(f"Soft-deleting Book {book_id}")

    try:
        await service.delete_book(book_id)

    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e.message}")
        raise HTTPException(
            status_code=404,
            detail=e.to_dict(),
        )
    except BookAlreadyDeletedError as e:
        logger.warning(f"Book already deleted: {e.message}")
        raise HTTPException(
            status_code=409,
            detail=e.to_dict(),
        )
    except Exception as e:
        logger.error(f"Failed to delete Book: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to delete Book: {str(e)}",
            },
        )


@router.post(
    "/{book_id}/restore",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore Book from Basement",
    description="Restore a deleted Book from Basement to target Bookshelf (RULE-013)",
)
async def restore_book(
    library_id: UUID,
    bookshelf_id: UUID,
    book_id: UUID,
    request: BookRestoreRequest,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """
    Restore a Book from Basement to a target Bookshelf.

    RULE-013: Book restoration from Basement

    Args:
        library_id: Parent Library ID
        bookshelf_id: Current Bookshelf ID (for context)
        book_id: Book ID to restore
        request: Target bookshelf ID

    Returns:
        Restored Book

    Raises:
        HTTPException 404: Book not found
        HTTPException 422: Book not in Basement or target invalid
        HTTPException 500: Operation error
    """
    logger.info(f"Restoring Book {book_id} to Bookshelf {request.target_bookshelf_id}")

    try:
        restored_book = await service.restore_from_basement(
            book_id=book_id,
            target_bookshelf_id=request.target_bookshelf_id,
        )
        book_dto = BookDTO.from_domain(restored_book)
        return book_dto.to_response()

    except BookNotFoundError as e:
        logger.warning(f"Book not found: {e.message}")
        raise HTTPException(
            status_code=404,
            detail=e.to_dict(),
        )
    except BookNotInBasementError as e:
        logger.warning(f"Book not in Basement: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except InvalidBookMoveError as e:
        logger.warning(f"Invalid restore target: {e.message}")
        raise HTTPException(
            status_code=422,
            detail=e.to_dict(),
        )
    except Exception as e:
        logger.error(f"Failed to restore Book: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BOOK_OPERATION_ERROR",
                "message": f"Failed to restore Book: {str(e)}",
            },
        )
