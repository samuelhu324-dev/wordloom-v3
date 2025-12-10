"""Search Domain Exceptions - Error definitions

POLICY: Comprehensive error handling for search operations.

Exception Hierarchy:
- SearchDomainException (base)
  ├─ InvalidQueryError (query validation)
  ├─ SearchNotFoundError (no results)
  ├─ SearchTimeoutError (query timeout)
  └─ SearchIndexError (index maintenance)
"""

from typing import Optional


class SearchDomainException(Exception):
    """Base exception for Search domain errors"""
    pass


class InvalidQueryError(SearchDomainException):
    """Raised when search query parameters are invalid"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(f"Invalid search query: {message}")


class SearchNotFoundError(SearchDomainException):
    """Raised when search returns no results (optional - for specific cases)"""

    def __init__(self, query: str, entity_type: Optional[str] = None):
        self.query = query
        self.entity_type = entity_type
        message = f"No results found for query: '{query}'"
        if entity_type:
            message += f" (type: {entity_type})"
        super().__init__(message)


class SearchTimeoutError(SearchDomainException):
    """Raised when search operation times out"""

    def __init__(self, query: str, timeout_ms: int):
        self.query = query
        self.timeout_ms = timeout_ms
        super().__init__(f"Search timeout after {timeout_ms}ms for query: '{query}'")


class SearchIndexError(SearchDomainException):
    """Raised when search index maintenance fails"""

    def __init__(self, operation: str, entity_type: str, entity_id: str, cause: str):
        self.operation = operation  # INSERT, UPDATE, DELETE
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            f"Search index {operation} failed for {entity_type}:{entity_id} - {cause}"
        )


__all__ = [
    "SearchDomainException",
    "InvalidQueryError",
    "SearchNotFoundError",
    "SearchTimeoutError",
    "SearchIndexError",
]
