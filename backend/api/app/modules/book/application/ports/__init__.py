"""
Book Ports - 所有 Input 和 Output Port 接口

Output Ports (repository.py):
  - BookRepository

Input Ports (input.py):
  - CreateBookUseCase
  - ListBooksUseCase
  - GetBookUseCase
  - UpdateBookUseCase
  - DeleteBookUseCase
  - RestoreBookUseCase
  - ListDeletedBooksUseCase

Request/Response DTOs:
  - CreateBookRequest, BookResponse
  - ListBooksRequest
  - UpdateBookRequest
  - ...
"""

# Output ports (repository)
from .output import BookRepository

# Input ports (use cases) + DTOs
from .input import (
    CreateBookUseCase,
    ListBooksUseCase,
    GetBookUseCase,
    UpdateBookUseCase,
    DeleteBookUseCase,
    RestoreBookUseCase,
    ListDeletedBooksUseCase,
    # Request DTOs
    CreateBookRequest,
    ListBooksRequest,
    GetBookRequest,
    UpdateBookRequest,
    DeleteBookRequest,
    RestoreBookRequest,
    ListDeletedBooksRequest,
    # Response DTOs
    BookResponse,
    BookListResponse,
)

__all__ = [
    # Output ports
    "BookRepository",
    # Input ports
    "CreateBookUseCase",
    "ListBooksUseCase",
    "GetBookUseCase",
    "UpdateBookUseCase",
    "DeleteBookUseCase",
    "RestoreBookUseCase",
    "ListDeletedBooksUseCase",
    # Request DTOs
    "CreateBookRequest",
    "ListBooksRequest",
    "GetBookRequest",
    "UpdateBookRequest",
    "DeleteBookRequest",
    "RestoreBookRequest",
    "ListDeletedBooksRequest",
    # Response DTOs
    "BookResponse",
    "BookListResponse",
]
