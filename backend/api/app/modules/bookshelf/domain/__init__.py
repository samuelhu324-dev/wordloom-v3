"""
Bookshelf Domain Layer - Public Interface

This module exports the public domain API for the Bookshelf module.
All external code should import from here, not from sub-modules.
"""

from .bookshelf import Bookshelf, BookshelfType, BookshelfStatus
from .bookshelf_name import BookshelfName
from .bookshelf_description import BookshelfDescription
from .events import (
    BookshelfCreated,
    BookshelfRenamed,
    BookshelfStatusChanged,
    BookshelfDeleted,
    BOOKSHELF_EVENTS,
)

__all__ = [
    # AggregateRoot
    "Bookshelf",
    # Enums
    "BookshelfType",
    "BookshelfStatus",
    # ValueObjects
    "BookshelfName",
    "BookshelfDescription",
    # Events
    "BookshelfCreated",
    "BookshelfRenamed",
    "BookshelfStatusChanged",
    "BookshelfDeleted",
    "BOOKSHELF_EVENTS",
]
