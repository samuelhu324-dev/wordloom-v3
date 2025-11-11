"""Media Tests"""
import pytest
from uuid import uuid4
from domains.media.domain import Media, MediaEntityType

@pytest.fixture
def sample_entity_id():
    return uuid4()

@pytest.fixture
def media_domain_factory(sample_entity_id):
    def _create(media_id=None, entity_type=MediaEntityType.BLOCK_IMAGE, entity_id=None):
        return Media(
            media_id=media_id or uuid4(),
            entity_type=entity_type,
            entity_id=entity_id or sample_entity_id,
            file_url="https://example.com/image.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            file_hash="abc123",
            width=800,
            height=600,
        )
    return _create

@pytest.fixture
async def mock_media_repository():
    class MockMediaRepository:
        def __init__(self):
            self.store = {}
        async def save(self, media: Media) -> None:
            self.store[media.id] = media
        async def get_by_id(self, media_id):
            return self.store.get(media_id)
        async def get_by_entity(self, entity_type, entity_id):
            return [m for m in self.store.values() if m.entity_type.value == entity_type and m.entity_id == entity_id]
        async def delete(self, media_id) -> None:
            self.store.pop(media_id, None)
    return MockMediaRepository()
