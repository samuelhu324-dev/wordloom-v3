"""
Bookshelf Domain Module

Public API exports for the Bookshelf aggregate root and related components.
"""

from .domain import Bookshelf, BookshelfName
from .service import BookshelfService
from .repository import BookshelfRepository, BookshelfRepositoryImpl
from .models import BookshelfModel
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
from .router import router

__all__ = [
    "Bookshelf",
    "BookshelfName",
    "BookshelfService",
    "BookshelfRepository",
    "BookshelfRepositoryImpl",
    "BookshelfModel",
    "BookshelfCreate",
    "BookshelfUpdate",
    "BookshelfResponse",
    "BookshelfDetailResponse",
    "BookshelfNotFoundError",
    "BookshelfAlreadyExistsError",
    "InvalidBookshelfNameError",
    "router",
]
