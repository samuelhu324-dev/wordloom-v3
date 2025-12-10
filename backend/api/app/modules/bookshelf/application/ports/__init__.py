"""
Bookshelf Ports - All Input and Output Port Interfaces

Output Ports (output.py):
  - IBookshelfRepository

Input Ports (input.py):
  - ICreateBookshelfUseCase
  - IGetBookshelfUseCase
  - IDeleteBookshelfUseCase
  - IRenameBookshelfUseCase

Request/Response DTOs:
  - CreateBookshelfRequest, CreateBookshelfResponse
  - GetBookshelfRequest, GetBookshelfResponse
  - DeleteBookshelfRequest
  - RenameBookshelfRequest, RenameBookshelfResponse
"""

# Output ports (repository)
from .output import IBookshelfRepository

# Input ports (use cases) + DTOs
from .input import (
    ICreateBookshelfUseCase,
    IGetBookshelfUseCase,
    IDeleteBookshelfUseCase,
    IRenameBookshelfUseCase,
    CreateBookshelfRequest,
    CreateBookshelfResponse,
    GetBookshelfRequest,
    GetBookshelfResponse,
    DeleteBookshelfRequest,
    RenameBookshelfRequest,
    RenameBookshelfResponse,
)

__all__ = [
    # Output ports
    "IBookshelfRepository",
    # Input ports
    "ICreateBookshelfUseCase",
    "IGetBookshelfUseCase",
    "IDeleteBookshelfUseCase",
    "IRenameBookshelfUseCase",
    # Request DTOs
    "CreateBookshelfRequest",
    "GetBookshelfRequest",
    "DeleteBookshelfRequest",
    "RenameBookshelfRequest",
    # Response DTOs
    "CreateBookshelfResponse",
    "GetBookshelfResponse",
    "RenameBookshelfResponse",
]
