"""
Book Domain Package

Exports public API of the Book domain layer.
"""

from .book import Book
from .book_title import BookTitle
from .book_summary import BookSummary
from .events import (
    BookStatus,
    BookMaturity,
    BookCreated,
    BookRenamed,
    BookStatusChanged,
    BookMaturityChanged,
    BookDeleted,
    BlocksUpdated,
    BookMovedToBookshelf,
    BookMovedToBasement,
    BookRestoredFromBasement,
)

__all__ = [
    # Aggregate
    "Book",
    # Value Objects
    "BookTitle",
    "BookSummary",
    # Enums
    "BookStatus",
    "BookMaturity",
    # Events
    "BookCreated",
    "BookRenamed",
    "BookStatusChanged",
    "BookMaturityChanged",
    "BookDeleted",
    "BlocksUpdated",
    "BookMovedToBookshelf",
    "BookMovedToBasement",
    "BookRestoredFromBasement",
]
