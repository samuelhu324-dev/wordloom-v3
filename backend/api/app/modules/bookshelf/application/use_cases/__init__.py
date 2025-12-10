"""
Bookshelf Application Layer - UseCase Implementations

Core 4 UseCases (Standard Pattern):
  - create_bookshelf.py  → CreateBookshelfUseCase(ICreateBookshelfUseCase)
  - get_bookshelf.py     → GetBookshelfUseCase(IGetBookshelfUseCase)
  - delete_bookshelf.py  → DeleteBookshelfUseCase(IDeleteBookshelfUseCase)
  - rename_bookshelf.py  → RenameBookshelfUseCase(IRenameBookshelfUseCase)

Design: Each UseCase orchestrates domain behavior with repository
- Validates business rules (RULE-006: name uniqueness, RULE-010: no Basement deletion)
- Calls domain methods (create, rename, mark_deleted)
- Handles persistence (save, queries)
- Publishes domain events implicitly
"""

from .create_bookshelf import CreateBookshelfUseCase
from .get_bookshelf import GetBookshelfUseCase
from .delete_bookshelf import DeleteBookshelfUseCase
from .rename_bookshelf import RenameBookshelfUseCase
from .update_bookshelf import UpdateBookshelfUseCase

__all__ = [
    "CreateBookshelfUseCase",
    "GetBookshelfUseCase",
    "DeleteBookshelfUseCase",
    "RenameBookshelfUseCase",
    "UpdateBookshelfUseCase",
]

