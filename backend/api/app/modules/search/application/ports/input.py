"""
Search Application Input Ports - UseCase Interfaces and DTOs

Defines the contract for search use cases with request/response DTOs.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class SearchHit(BaseModel):
    """Single search result hit"""
    entity_id: UUID
    entity_type: str
    title: str
    description: Optional[str] = None
    matched_text: Optional[str] = None


class ExecuteSearchRequest(BaseModel):
    """Request to execute global search"""
    q: str
    entity_type: Optional[str] = None
    book_id: Optional[UUID] = None
    limit: int = 20
    offset: int = 0


class ExecuteSearchResponse(BaseModel):
    """Response from search execution"""
    hits: List[SearchHit]
    total: int
    limit: int
    offset: int


class ExecuteSearchUseCase(ABC):
    """Execute Search UseCase - Port (Input Adapter)

    Orchestrates search across all entities.
    Application layer depends on SearchPort (output port).
    """

    @abstractmethod
    async def execute(self, request: ExecuteSearchRequest) -> ExecuteSearchResponse:
        """Execute search operation

        Args:
            request: Search parameters
                - q: Search query text (required)
                - entity_type: Optional filter (None = global search)
                - book_id: Optional book scope limitation
                - limit: Pagination size
                - offset: Pagination offset

        Returns:
            ExecuteSearchResponse with hits and total count

        Raises:
            InvalidQueryError: Invalid search parameters
            SearchIndexError: Search engine failure
        """
        pass


__all__ = [
    "SearchHit",
    "ExecuteSearchRequest",
    "ExecuteSearchResponse",
    "ExecuteSearchUseCase",
]
