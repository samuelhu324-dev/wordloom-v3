"""
Bookshelf Ports - 所有 Input 和 Output Port 接口

Output Ports (repository.py):
  - BookshelfRepository

Input Ports (input.py):
  - CreateBookshelfUseCase
  - ListBookshelvesUseCase
  - GetBookshelfUseCase
  - UpdateBookshelfUseCase
  - DeleteBookshelfUseCase
  - GetBasementUseCase

Request/Response DTOs:
  - CreateBookshelfRequest, BookshelfResponse
  - ListBookshelvesRequest
  - UpdateBookshelfRequest
  - ...
"""

# Output ports (repository)
from .output import BookshelfRepository

# Input ports (use cases) + DTOs
from .input import (
    CreateBookshelfUseCase,
    ListBookshelvesUseCase,
    GetBookshelfUseCase,
    UpdateBookshelfUseCase,
    DeleteBookshelfUseCase,
    GetBasementUseCase,
    # Request DTOs
    CreateBookshelfRequest,
    ListBookshelvesRequest,
    GetBookshelfRequest,
    UpdateBookshelfRequest,
    DeleteBookshelfRequest,
    GetBasementRequest,
    # Response DTOs
    BookshelfResponse,
)

__all__ = [
    # Output ports
    "BookshelfRepository",
    # Input ports
    "CreateBookshelfUseCase",
    "ListBookshelvesUseCase",
    "GetBookshelfUseCase",
    "UpdateBookshelfUseCase",
    "DeleteBookshelfUseCase",
    "GetBasementUseCase",
    # Request DTOs
    "CreateBookshelfRequest",
    "ListBookshelvesRequest",
    "GetBookshelfRequest",
    "UpdateBookshelfRequest",
    "DeleteBookshelfRequest",
    "GetBasementRequest",
    # Response DTOs
    "BookshelfResponse",
]
