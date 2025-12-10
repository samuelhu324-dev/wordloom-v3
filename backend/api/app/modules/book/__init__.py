"""
Book Module - Hexagonal Architecture

Public API exports for the Book aggregate root and related components.

Architecture:
- Domain Layer: Pure business logic (Book, BookTitle, BookSummary, Events)
- Application Layer: UseCase implementations
- Infrastructure Layer: Adapters (ORM, Repository)
- HTTP Layer: FastAPI router and schemas
"""

# Domain Layer - Pure business logic
from .domain import (
    Book,
    BookTitle,
    BookSummary,
    BookStatus,
    BookCreated,
    BookRenamed,
    BookStatusChanged,
    BookDeleted,
    BlocksUpdated,
    BookMovedToBookshelf,
    BookMovedToBasement,
    BookRestoredFromBasement,
)

# Application Layer - UseCase Implementations
from .application.use_cases import (
    CreateBookUseCase,
    ListBooksUseCase,
    GetBookUseCase,
    UpdateBookUseCase,
    DeleteBookUseCase,
    RestoreBookUseCase,
    MoveBookUseCase,
    ListDeletedBooksUseCase,
)

# HTTP Layer - Schemas and DTOs
from .schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookDTO,
    BookRestoreRequest,
)

# HTTP Layer - Exceptions with HTTP status codes
from .exceptions import (
    BookNotFoundError,
    InvalidBookTitleError,
    BookOperationError,
)

# HTTP Layer - FastAPI Router (conditional import to avoid failures during testing)
try:
    from .routers.book_router import router
except Exception:
    # Router import failed, set to None (testing mode)
    router = None

__all__ = [
    # Domain
    "Book",
    "BookTitle",
    "BookSummary",
    "BookStatus",
    "BookCreated",
    "BookRenamed",
    "BookStatusChanged",
    "BookDeleted",
    "BlocksUpdated",
    "BookMovedToBookshelf",
    "BookMovedToBasement",
    "BookRestoredFromBasement",
    # Application - UseCases
    "CreateBookUseCase",
    "ListBooksUseCase",
    "GetBookUseCase",
    "UpdateBookUseCase",
    "DeleteBookUseCase",
    "RestoreBookUseCase",
    "MoveBookUseCase",
    "ListDeletedBooksUseCase",
    # HTTP
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookDetailResponse",
    "BookDTO",
    "BookRestoreRequest",
    "BookNotFoundError",
    "InvalidBookTitleError",
    "BookOperationError",
    "router",
]
