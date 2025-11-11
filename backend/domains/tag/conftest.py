"""Tag Tests"""
import pytest
from uuid import uuid4
from domains.tag.domain import Tag, TagName, TagColor

@pytest.fixture
def tag_domain_factory():
    def _create(tag_id=None, name="Test Tag", color="#FF0000"):
        return Tag(
            tag_id=tag_id or uuid4(),
            name=TagName(value=name),
            color=TagColor(value=color),
        )
    return _create

@pytest.fixture
async def mock_tag_repository():
    class MockTagRepository:
        def __init__(self):
            self.store = {}
        async def save(self, tag: Tag) -> None:
            self.store[tag.id] = tag
        async def get_by_id(self, tag_id):
            return self.store.get(tag_id)
        async def get_by_name(self, name):
            for tag in self.store.values():
                if tag.name.value == name: return tag
            return None
        async def list_all(self):
            return list(self.store.values())
        async def delete(self, tag_id) -> None:
            self.store.pop(tag_id, None)
    return MockTagRepository()
