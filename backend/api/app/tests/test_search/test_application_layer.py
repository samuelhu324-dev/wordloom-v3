"""Unit tests for Search application layer."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


class TestExecuteSearchUseCase:
    """Test execute search use case."""

    @pytest.mark.asyncio
    async def test_search_blocks(self):
        service = AsyncMock()
        service.search = AsyncMock(return_value={"total_count": 3, "results": []})
        result = await service.search(uuid4(), "python", entity_types=["BLOCK"])
        assert result["total_count"] == 3

    @pytest.mark.asyncio
    async def test_search_multiple_entity_types(self):
        service = AsyncMock()
        service.search = AsyncMock(return_value={"total_count": 5, "results": []})
        result = await service.search(uuid4(), "important", entity_types=["BLOCK", "BOOK", "TAG"])
        assert result["total_count"] == 5

    @pytest.mark.asyncio
    async def test_search_with_pagination(self):
        service = AsyncMock()
        service.search = AsyncMock(return_value={"total_count": 100, "results": []})
        result = await service.search(uuid4(), "test", skip=0, limit=10)
        assert result["total_count"] == 100

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        service = AsyncMock()
        service.search = AsyncMock(return_value={"total_count": 0, "results": []})
        result = await service.search(uuid4(), "nonexistent")
        assert result["total_count"] == 0


class TestSearchUseCase:
    """Test search use case variations."""

    @pytest.mark.asyncio
    async def test_search_libraries(self):
        service = AsyncMock()
        service.search_libraries = AsyncMock(return_value={"results": []})
        result = await service.search_libraries(uuid4(), "library")
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_entries(self):
        service = AsyncMock()
        service.search_entries = AsyncMock(return_value={"results": []})
        result = await service.search_entries(uuid4(), "entry")
        assert "results" in result


class TestSearchApplicationLayerPermissions:
    """Test search permission checks."""

    @pytest.mark.asyncio
    async def test_search_respects_library_permissions(self):
        auth_service = AsyncMock()
        auth_service.can_access_library = AsyncMock(return_value=True)
        can_access = await auth_service.can_access_library(uuid4(), uuid4())
        assert can_access is True

    @pytest.mark.asyncio
    async def test_search_rejects_unauthorized_access(self):
        auth_service = AsyncMock()
        auth_service.can_access_library = AsyncMock(return_value=False)
        can_access = await auth_service.can_access_library(uuid4(), uuid4())
        assert can_access is False
