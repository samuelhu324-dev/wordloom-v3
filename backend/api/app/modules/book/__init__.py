"""
Book Domain Module

Public API exports for the Book aggregate root and related components.
"""

from .domain import Book, BookTitle
from .service import BookService
from .repository import BookRepository, BookRepositoryImpl
from .models import BookModel
from .schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
)
from .exceptions import (
    BookNotFoundError,
    InvalidBookTitleError,
    BookOperationError,
)
from .router import router

__all__ = [
    "Book",
    "BookTitle",
    "BookService",
    "BookRepository",
    "BookRepositoryImpl",
    "BookModel",
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookDetailResponse",
    "BookNotFoundError",
    "InvalidBookTitleError",
    "BookOperationError",
    "router",
]
