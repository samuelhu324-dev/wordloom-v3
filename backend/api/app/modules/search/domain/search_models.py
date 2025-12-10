"""
Search Domain Models - ValueObjects for Query and Results

Pure domain layer: No infrastructure, no dependencies on other modules.
Represents the contract between HTTP adapter and search engine.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from uuid import UUID
from enum import Enum as PyEnum


class SearchEntityType(PyEnum):
    """Entity types that can be searched"""
    BLOCK = "block"
    BOOK = "book"
    BOOKSHELF = "bookshelf"
    TAG = "tag"
    LIBRARY = "library"


@dataclass
class SearchQuery:
    """Search Query - ValueObject

    Immutable search parameters passed to SearchPort.
    Can represent global search or scoped search (book_id filter).
    """
    text: str
    type: Optional[SearchEntityType] = None  # None = global search all types
    book_id: Optional[UUID] = None           # Scope search to a specific book
    limit: int = 20
    offset: int = 0

    def __post_init__(self):
        """Validate search query parameters"""
        if not self.text or not self.text.strip():
            raise ValueError("Search text cannot be empty")
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")
        # Strip whitespace
        object.__setattr__(self, "text", self.text.strip())


@dataclass
class SearchHit:
    """Single search result - ValueObject

    Represents one entity match from the search.
    Includes metadata for display and ranking.
    """
    entity_type: SearchEntityType
    entity_id: UUID
    title: str
    snippet: str              # Preview text (first 200 chars)
    score: float              # Relevance score (0-1)
    path: str                 # Breadcrumb: "Library A / Shelf B / Book C"
    rank_algorithm: str = "ts_rank_cd"  # Which ranking algorithm produced this score

    def __post_init__(self):
        """Validate search hit"""
        if not self.title or not self.title.strip():
            raise ValueError("Hit title cannot be empty")
        if self.score < 0 or self.score > 1:
            raise ValueError("Score must be between 0 and 1")


@dataclass
class SearchResult:
    """Search Result Set - ValueObject

    Complete result from a search operation.
    Includes hits and total count for pagination.
    """
    total: int
    hits: List[SearchHit] = field(default_factory=list)
    query: Optional[SearchQuery] = None  # The query that produced these results

    def __post_init__(self):
        """Validate search result"""
        if self.total < 0:
            raise ValueError("Total count cannot be negative")
        if len(self.hits) > (self.query.limit if self.query else 1000):
            raise ValueError("Hit count exceeds limit")


__all__ = [
    "SearchEntityType",
    "SearchQuery",
    "SearchHit",
    "SearchResult",
]
