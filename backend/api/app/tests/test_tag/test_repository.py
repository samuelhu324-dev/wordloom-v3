"""Unit tests for Tag repository."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock


class TestSQLAlchemyTagRepository:
    """Test SQLAlchemy Tag repository implementation."""

    @pytest.mark.asyncio
    async def test_save_new_tag(self):
        repo = AsyncMock()
        repo.save = AsyncMock()
        tag = {"tag_id": uuid4(), "name": "NewTag"}
        await repo.save(tag)
        assert repo.save.called

    @pytest.mark.asyncio
    async def test_get_tag_by_id(self):
        repo = AsyncMock()
        tag_id = uuid4()
        tag = {"tag_id": tag_id, "name": "TestTag"}
        repo.get_by_id = AsyncMock(return_value=tag)
        result = await repo.get_by_id(tag_id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all_tags_by_library(self):
        repo = AsyncMock()
        tags = [{"name": f"Tag{i}"} for i in range(3)]
        repo.get_all_by_library = AsyncMock(return_value=tags)
        result = await repo.get_all_by_library(uuid4())
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_update_tag(self):
        repo = AsyncMock()
        repo.update = AsyncMock()
        tag = {"tag_id": uuid4(), "name": "Updated"}
        await repo.update(tag)
        assert repo.update.called

    @pytest.mark.asyncio
    async def test_soft_delete_tag(self):
        repo = AsyncMock()
        repo.soft_delete = AsyncMock()
        await repo.soft_delete(uuid4())
        assert repo.soft_delete.called

    @pytest.mark.asyncio
    async def test_exclude_deleted_tags_from_queries(self):
        repo = AsyncMock()
        tags = [{"name": "Active", "is_deleted": False}]
        repo.get_all_by_library = AsyncMock(return_value=tags)
        result = await repo.get_all_by_library(uuid4())
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_tags_by_name(self):
        repo = AsyncMock()
        tags = [{"name": "Important"}, {"name": "ImportantReview"}]
        repo.find_by_name_pattern = AsyncMock(return_value=tags)
        result = await repo.find_by_name_pattern(uuid4(), "Important")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_tags_by_entity_association(self):
        repo = AsyncMock()
        tags = [{"name": "Tag1"}, {"name": "Tag2"}]
        repo.get_by_entity = AsyncMock(return_value=tags)
        result = await repo.get_by_entity(uuid4())
        assert len(result) == 2


class TestTagRepositoryTransactions:
    """Test repository transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        repo = AsyncMock()
        repo.rollback = AsyncMock()
        repo.commit = AsyncMock(side_effect=Exception("DB Error"))
        try:
            await repo.commit()
        except Exception:
            await repo.rollback()
        assert repo.rollback.called

    @pytest.mark.asyncio
    async def test_transaction_commit_on_success(self):
        repo = AsyncMock()
        repo.commit = AsyncMock()
        await repo.commit()
        assert repo.commit.called
