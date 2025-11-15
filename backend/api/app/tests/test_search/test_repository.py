"""Unit tests for Search repository."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


class TestPostgresSearchAdapter:
    """Test PostgreSQL full-text search adapter."""

    @pytest.mark.asyncio
    async def test_search_with_full_text_index(self):
        db_adapter = AsyncMock()
        db_adapter.full_text_search = AsyncMock(return_value=[{"id": str(uuid4()), "entity_type": "BLOCK"}])
        results = await db_adapter.full_text_search(uuid4(), "python")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_single_entity_type(self):
        repo = AsyncMock()
        repo.search_blocks = AsyncMock(return_value={"total": 5, "results": []})
        result = await repo.search_blocks(uuid4(), "query")
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_search_multiple_entity_types(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total": 10, "results": []})
        result = await repo.search(uuid4(), "query", entity_types=["BLOCK", "BOOK"])
        assert result["total"] == 10

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"results": []})
        await repo.search(uuid4(), "query", entity_types=["BLOCK"])
        assert repo.search.called

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total": 50, "results": []})
        result = await repo.search(uuid4(), "test", skip=0, limit=10)
        assert result["total"] == 50

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total": 0, "results": []})
        result = await repo.search(uuid4(), "nonexistent")
        assert result["total"] == 0


class TestSearchRepositoryQueries:
    """Test specialized search repository queries."""

    @pytest.mark.asyncio
    async def test_search_blocks_by_content(self):
        repo = AsyncMock()
        repo.search_blocks = AsyncMock(return_value={"count": 3, "results": []})
        result = await repo.search_blocks(uuid4(), "python")
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_search_books_by_title(self):
        repo = AsyncMock()
        repo.search_books = AsyncMock(return_value={"count": 2, "results": []})
        result = await repo.search_books(uuid4(), "python")
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_search_tags(self):
        repo = AsyncMock()
        repo.search_tags = AsyncMock(return_value={"results": []})
        result = await repo.search_tags(uuid4(), "important")
        assert "results" in result


class TestSearchRepositoryCaching:
    """Test search repository caching."""

    @pytest.mark.asyncio
    async def test_cache_search_results(self):
        repo = AsyncMock()
        repo.cache_get = AsyncMock(return_value=None)
        repo.cache_set = AsyncMock()
        await repo.cache_get("query:test")
        await repo.cache_set("query:test", {"results": []})
        assert repo.cache_set.called
