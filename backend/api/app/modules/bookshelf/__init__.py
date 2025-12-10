"""
Bookshelf Domain Module

Public API exports for the Bookshelf aggregate root and related components.
"""

from .domain import Bookshelf, BookshelfName, BookshelfDescription, BookshelfType, BookshelfStatus
from .application.ports.input import (
    ICreateBookshelfUseCase,
    IGetBookshelfUseCase,
    IDeleteBookshelfUseCase,
    IRenameBookshelfUseCase,
)
from .schemas import (
    BookshelfCreate,
    BookshelfUpdate,
    BookshelfResponse,
    BookshelfDetailResponse,
)
from .exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
    InvalidBookshelfNameError,
)
# Router import commented out - requires DI container, not needed for tests
# from .routers import bookshelf_router

__all__ = [
    # Domain
    "Bookshelf",
    "BookshelfName",
    "BookshelfDescription",
    "BookshelfType",
    "BookshelfStatus",
    # UseCases
    "ICreateBookshelfUseCase",
    "IGetBookshelfUseCase",
    "IDeleteBookshelfUseCase",
    "IRenameBookshelfUseCase",
    # Schemas
    "BookshelfCreate",
    "BookshelfUpdate",
    "BookshelfResponse",
    "BookshelfDetailResponse",
    # Exceptions
    "BookshelfNotFoundError",
    "BookshelfAlreadyExistsError",
    "InvalidBookshelfNameError",
    # Router (commented)
    # "bookshelf_router",
]
