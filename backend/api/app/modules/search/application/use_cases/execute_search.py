"""
Execute Search UseCase Implementation

Business logic orchestration layer.
Depends on SearchPort (output port).
"""

import logging
from typing import Optional

from modules.search.application.ports.input import (
    ExecuteSearchRequest,
    ExecuteSearchResponse,
    SearchHitResponse,
    ExecuteSearchUseCase,
)
from modules.search.application.ports.output import SearchPort
from modules.search.domain import SearchQuery, SearchEntityType

logger = logging.getLogger(__name__)


class ExecuteSearchService(ExecuteSearchUseCase):
    """Execute Search UseCase - Service Implementation

    Orchestrates search across multiple entity types.
    Converts HTTP DTOs â†?Domain models.
    Delegates to SearchPort for actual search implementation.
    """

    def __init__(self, search_port: SearchPort):
        """Initialize with search port

        Args:
            search_port: SearchPort implementation (injected)
        """
        self.search_port = search_port

    async def execute(self, request: ExecuteSearchRequest) -> ExecuteSearchResponse:
        """Execute search operation

        Args:
            request: ExecuteSearchRequest (text, type, book_id, limit, offset)

        Returns:
            ExecuteSearchResponse with hits and total count
        """
        try:
            # Build domain SearchQuery
            entity_type = None
            if request.type:
                entity_type = SearchEntityType(request.type)

            query = SearchQuery(
                text=request.text,
                type=entity_type,
                book_id=request.book_id,
                limit=request.limit,
                offset=request.offset,
            )

            # Route to appropriate search method based on type
            if query.type == SearchEntityType.BLOCK:
                result = await self.search_port.search_blocks(query)
            elif query.type == SearchEntityType.BOOK:
                result = await self.search_port.search_books(query)
            elif query.type == SearchEntityType.BOOKSHELF:
                result = await self.search_port.search_bookshelves(query)
            elif query.type == SearchEntityType.TAG:
                result = await self.search_port.search_tags(query)
            elif query.type == SearchEntityType.LIBRARY:
                result = await self.search_port.search_libraries(query)
            elif query.type == SearchEntityType.ENTRY:
                result = await self.search_port.search_entries(query)
            else:
                # Global search: aggregate results from all types
                results = await self._search_all(query)
                return ExecuteSearchResponse(
                    total=results.total,
                    hits=[
                        SearchHitResponse(
                            entity_type=hit.entity_type.value,
                            entity_id=str(hit.entity_id),
                            title=hit.title,
                            snippet=hit.snippet,
                            score=hit.score,
                            path=hit.path,
                            rank_algorithm=hit.rank_algorithm,
                        )
                        for hit in results.hits
                    ],
                )

            # Convert domain result to DTO
            return ExecuteSearchResponse(
                total=result.total,
                hits=[
                    SearchHitResponse(
                        entity_type=hit.entity_type.value,
                        entity_id=str(hit.entity_id),
                        title=hit.title,
                        snippet=hit.snippet,
                        score=hit.score,
                        path=hit.path,
                        rank_algorithm=hit.rank_algorithm,
                    )
                    for hit in result.hits
                ],
            )

        except ValueError as e:
            logger.warning(f"Invalid search query: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Search execution failed: {str(e)}")
            raise

    async def _search_all(self, query: SearchQuery):
        """Execute parallel search across all entity types

        Args:
            query: SearchQuery

        Returns:
            Aggregated SearchResult from all types
        """
        import asyncio

        # Execute all searches in parallel
        block_result, book_result, bookshelf_result, tag_result, library_result, entry_result = await asyncio.gather(
            self.search_port.search_blocks(query),
            self.search_port.search_books(query),
            self.search_port.search_bookshelves(query),
            self.search_port.search_tags(query),
            self.search_port.search_libraries(query),
            self.search_port.search_entries(query),
        )

        # Aggregate results
        all_hits = (
            block_result.hits +
            book_result.hits +
            bookshelf_result.hits +
            tag_result.hits +
            library_result.hits +
            entry_result.hits
        )

        # Sort by score descending
        all_hits.sort(key=lambda h: h.score, reverse=True)

        # Truncate to limit
        paginated_hits = all_hits[query.offset:query.offset + query.limit]

        from modules.search.domain import SearchResult
        return SearchResult(
            total=len(all_hits),
            hits=paginated_hits,
            query=query,
        )


__all__ = [
    "ExecuteSearchService",
]
