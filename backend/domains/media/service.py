"""Media Service"""
from typing import List
from uuid import UUID
from domains.media.domain import Media, MediaEntityType
from domains.media.repository import MediaRepository

class MediaService:
    def __init__(self, repository: MediaRepository):
        self.repository = repository

    async def upload_media(self, entity_type: str, entity_id: UUID, file_url: str, file_size: int, mime_type: str, file_hash: str, width: int = None, height: int = None) -> Media:
        et = MediaEntityType(entity_type)
        media = Media.create(et, entity_id, file_url, file_size, mime_type, file_hash, width, height)
        await self.repository.save(media)
        return media

    async def get_media(self, media_id: UUID) -> Media:
        media = await self.repository.get_by_id(media_id)
        if not media: raise Exception(f"Media {media_id} not found")
        return media

    async def get_entity_media(self, entity_type: str, entity_id: UUID) -> List[Media]:
        return await self.repository.get_by_entity(entity_type, entity_id)

    async def delete_media(self, media_id: UUID) -> None:
        media = await self.get_media(media_id)
        media.mark_deleted()
        await self.repository.save(media)
        await self.repository.delete(media_id)
