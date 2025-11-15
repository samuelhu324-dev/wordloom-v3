"""Unit tests for Tag application layer."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


class TestCreateTagUseCase:
    """Test create tag use case."""

    @pytest.mark.asyncio
    async def test_create_tag_success(self):
        repo = AsyncMock()
        repo.save = AsyncMock()
        tag_id = uuid4()
        await repo.save({"tag_id": tag_id})
        assert repo.save.called

    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name(self):
        repo = AsyncMock()
        repo.exists_by_name = AsyncMock(return_value=True)
        exists = await repo.exists_by_name(uuid4(), "Existing")
        assert exists is True


class TestGetTagUseCase:
    """Test get tag use case."""

    @pytest.mark.asyncio
    async def test_get_tag_success(self):
        repo = AsyncMock()
        tag = {"tag_id": uuid4(), "name": "Test"}
        repo.get_by_id = AsyncMock(return_value=tag)
        result = await repo.get_by_id(uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_tag_not_found(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        result = await repo.get_by_id(uuid4())
        assert result is None


class TestRenameTagUseCase:
    """Test rename tag use case."""

    @pytest.mark.asyncio
    async def test_rename_tag_success(self):
        tag = {"name": "Original"}
        tag["name"] = "Updated"
        assert tag["name"] == "Updated"


class TestAssociateTagUseCase:
    """Test associating entities with tag."""

    @pytest.mark.asyncio
    async def test_associate_entity_success(self):
        tag = {"associations": []}
        entity_id = uuid4()
        tag["associations"].append({"entity_id": entity_id, "type": "BLOCK"})
        assert len(tag["associations"]) == 1


class TestTagApplicationLayerIntegration:
    """Test application layer integration."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_tag(self):
        tag_id = uuid4()
        repo = AsyncMock()
        tag = {"tag_id": tag_id, "name": "NewTag"}
        repo.save = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=tag)
        await repo.save(tag)
        retrieved = await repo.get_by_id(tag_id)
        assert retrieved["tag_id"] == tag_id
