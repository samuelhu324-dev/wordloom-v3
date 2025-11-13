"""
Storage Module - Repository Adapters

Contains concrete implementations of repository ports defined in:
  modules/{name}/application/ports/output.py

Modules (one per domain):
  - tag_repository_impl.py: SQLAlchemyTagRepository
  - media_repository_impl.py: SQLAlchemyMediaRepository
  - library_repository_impl.py: SQLAlchemyLibraryRepository
  - bookshelf_repository_impl.py: SQLAlchemyBookshelfRepository
  - book_repository_impl.py: SQLAlchemyBookRepository
  - block_repository_impl.py: SQLAlchemyBlockRepository

These adapters are injected into use cases via DI container.
"""

from .tag_repository_impl import SQLAlchemyTagRepository
from .media_repository_impl import SQLAlchemyMediaRepository
from .library_repository_impl import SQLAlchemyLibraryRepository
from .bookshelf_repository_impl import SQLAlchemyBookshelfRepository
from .book_repository_impl import SQLAlchemyBookRepository
from .block_repository_impl import SQLAlchemyBlockRepository

__all__ = [
    "SQLAlchemyTagRepository",
    "SQLAlchemyMediaRepository",
    "SQLAlchemyLibraryRepository",
    "SQLAlchemyBookshelfRepository",
    "SQLAlchemyBookRepository",
    "SQLAlchemyBlockRepository",
]

