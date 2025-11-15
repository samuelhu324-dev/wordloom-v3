"""Search Domain - Unified public API

Import all domain models, enums, exceptions from this single entry point.
Follows Media module pattern: enums.py, search.py, exceptions.py, events.py
"""

from .enums import SearchEntityType, SearchMediaType
from .search import SearchQuery, SearchHit, SearchResult
from .exceptions import (
    SearchDomainException,
    InvalidQueryError,
    SearchNotFoundError,
    SearchTimeoutError,
    SearchIndexError,
)
from .events import SearchIndexUpdated

__all__ = [
    # Enums
    "SearchEntityType",
    "SearchMediaType",
    # ValueObjects
    "SearchQuery",
    "SearchHit",
    "SearchResult",
    # Exceptions
    "SearchDomainException",
    "InvalidQueryError",
    "SearchNotFoundError",
    "SearchTimeoutError",
    "SearchIndexError",
    # Events
    "SearchIndexUpdated",
]
