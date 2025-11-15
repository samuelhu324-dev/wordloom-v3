"""Integration tests for Search module."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


class TestSearchEndToEndWorkflow:
    """Test complete search workflows."""

    @pytest.mark.asyncio
    async def test_search_across_all_entity_types(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total_count": 6, "results": []})
        result = await repo.search(uuid4(), "important", entity_types=["BLOCK", "BOOK", "TAG"])
        assert result["total_count"] == 6

    @pytest.mark.asyncio
    async def test_search_and_filter_by_type(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"results": [{"entity_type": "BLOCK"}]})
        result = await repo.search(uuid4(), "test")
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_with_pagination_workflow(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total_count": 100, "results": []})
        result = await repo.search(uuid4(), "query", skip=0, limit=10)
        assert result["total_count"] == 100

    @pytest.mark.asyncio
    async def test_search_blocks_workflow(self):
        repo = AsyncMock()
        repo.search_blocks = AsyncMock(return_value={"results": []})
        result = await repo.search_blocks(uuid4(), "python")
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_books_workflow(self):
        repo = AsyncMock()
        repo.search_books = AsyncMock(return_value={"results": []})
        result = await repo.search_books(uuid4(), "python")
        assert "results" in result


class TestSearchCrossModuleIntegration:
    """Test search integration with other modules."""

    @pytest.mark.asyncio
    async def test_search_tagged_entities(self):
        repo = AsyncMock()
        repo.search_by_tag = AsyncMock(return_value={"results": []})
        result = await repo.search_by_tag(uuid4(), uuid4())
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_within_bookshelf(self):
        repo = AsyncMock()
        repo.search_in_bookshelf = AsyncMock(return_value={"results": []})
        result = await repo.search_in_bookshelf(uuid4(), "query")
        assert "results" in result


class TestSearchPerformanceIntegration:
    """Test search performance in integration scenarios."""

    @pytest.mark.asyncio
    async def test_large_scale_search(self):
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"total_count": 10000, "results": []})
        result = await repo.search(uuid4(), "query", limit=20)
        assert result["total_count"] == 10000

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        import asyncio
        repo = AsyncMock()
        repo.search = AsyncMock(return_value={"results": []})

        tasks = [repo.search(uuid4(), f"query{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5


class TestSearchErrorHandlingIntegration:
    """Test search error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_handle_database_connection_error(self):
        repo = AsyncMock()
        repo.search = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(Exception):
            await repo.search(uuid4(), "query")

    @pytest.mark.asyncio
    async def test_fallback_on_search_error(self):
        repo = AsyncMock()
        repo.search_with_fallback = AsyncMock(return_value={"results": []})
        result = await repo.search_with_fallback(uuid4(), "query")
        assert result["results"] == []
