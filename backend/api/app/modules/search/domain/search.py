"""Search Domain Models - ValueObjects and AggregateRoot

Pure domain layer: No infrastructure, no dependencies on other modules.
Represents the contract between HTTP adapter and search engine.

Domain model philosophy:
- SearchQuery: ValueObject (immutable search parameters)
- SearchHit: ValueObject (immutable search result)
- SearchResult: ValueObject (immutable result set)
- No AggregateRoot: Search is a query adapter, not a managed entity

All domain logic and invariants implemented in __post_init__ validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID

from .enums import SearchEntityType
from .exceptions import InvalidQueryError


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class SearchQuery:
    """
    Search Query - ValueObject

    Immutable search parameters passed to SearchPort.
    Can represent global search or scoped search (book_id filter).

    Invariants:
    - text: non-empty, 1-500 chars
    - limit: 1-1000
    - offset: >= 0
    """
    text: str
    type: Optional[SearchEntityType] = None  # None = global search all types
    book_id: Optional[UUID] = None           # Scope search to a specific book
    limit: int = 20
    offset: int = 0

    def __post_init__(self):
        """Validate search query parameters"""
        if not self.text or not self.text.strip():
            raise InvalidQueryError("Search text cannot be empty", field="text")
        if len(self.text) > 500:
            raise InvalidQueryError("Search text exceeds 500 chars", field="text")
        if self.limit <= 0 or self.limit > 1000:
            raise InvalidQueryError("Limit must be between 1 and 1000", field="limit")
        if self.offset < 0:
            raise InvalidQueryError("Offset must be non-negative", field="offset")
        # Strip whitespace (immutable: use object.__setattr__)
        object.__setattr__(self, "text", self.text.strip())


@dataclass(frozen=True)
class SearchHit:
    """
    Single search result - ValueObject

    Represents one entity match from the search.
    Includes metadata for display and ranking.rank

    Invariants:
    - title: non-empty
    - score: 0-1
    - entity_id: valid UUID
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


@dataclass(frozen=True)
class SearchResult:
    """
    Search Result Set - ValueObject

    Complete result from a search operation.
    Includes hits and total count for pagination.

    Invariants:
    - total: >= 0
    - hits count: <= limit
    """
    total: int
    hits: List[SearchHit] = field(default_factory=list)
    query: Optional[SearchQuery] = None  # The query that produced these results

    def __post_init__(self):
        """Validate search result"""
        if self.total < 0:
            raise ValueError("Total count cannot be negative")
        if self.query and len(self.hits) > self.query.limit:
            raise ValueError("Hit count exceeds limit")


__all__ = [
    "SearchQuery",
    "SearchHit",
    "SearchResult",
]
