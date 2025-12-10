"""
Search Application Output Ports - Repository Abstraction

Defines the contract for search backend implementation.
Allows switching between PostgreSQL, Elasticsearch, etc.
"""

from abc import ABC, abstractmethod
from typing import List

from api.app.modules.search.domain import SearchQuery, SearchHit, SearchResult


class SearchPort(ABC):
    """Search Output Port - Abstract Repository

    Hexagonal Port: System boundary for search operations.
    Can be implemented via:
      - PostgresSearchAdapter (current: search_index table)
      - ElasticsearchAdapter (future: Elastic cluster)
      - OpenSearchAdapter (future: OpenSearch)

    Key property: Port interface NEVER changes.
    All evolution happens in adapter implementations.
    """

    @abstractmethod
    async def search_blocks(self, query: SearchQuery) -> SearchResult:
        """Search blocks

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching blocks

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass

    @abstractmethod
    async def search_books(self, query: SearchQuery) -> SearchResult:
        """Search books

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching books

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass

    @abstractmethod
    async def search_bookshelves(self, query: SearchQuery) -> SearchResult:
        """Search bookshelves - Find bookshelves matching search criteria

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching bookshelves

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass

    @abstractmethod
    async def search_tags(self, query: SearchQuery) -> SearchResult:
        """Search tags

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching tags

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass

    @abstractmethod
    async def search_libraries(self, query: SearchQuery) -> SearchResult:
        """Search libraries - Find libraries matching search criteria

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching libraries

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass

    @abstractmethod
    async def search_entries(self, query: SearchQuery) -> SearchResult:
        """Search entries (Loom terms) - Find entries matching search criteria

        Args:
            query: SearchQuery with text, filters, pagination

        Returns:
            SearchResult with matching entries

        Raises:
            SearchIndexError: Backend failure
            InvalidSearchQuery: Query validation failed
        """
        pass


__all__ = [
    "SearchPort",
]
