"""Media Repository"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domains.media.domain import Media, MediaEntityType
from domains.media.models import MediaModel

class MediaRepository(ABC):
    @abstractmethod
    async def save(self, media: Media) -> None: pass
    @abstractmethod
    async def get_by_id(self, media_id: UUID) -> Optional[Media]: pass
    @abstractmethod
    async def get_by_entity(self, entity_type: str, entity_id: UUID) -> List[Media]: pass
    @abstractmethod
    async def delete(self, media_id: UUID) -> None: pass

class MediaRepositoryImpl(MediaRepository):
    def __init__(self, session):
        self.session = session

    async def save(self, media: Media) -> None:
        model = MediaModel(
            id=media.id,
            entity_type=media.entity_type.value,
            entity_id=media.entity_id,
            file_url=media.file_url,
            file_size=media.file_size,
            mime_type=media.mime_type,
            file_hash=media.file_hash,
            width=media.width,
            height=media.height,
            created_at=media.created_at,
            updated_at=media.updated_at,
            deleted_at=media.deleted_at,
        )
        self.session.add(model)

    async def get_by_id(self, media_id: UUID) -> Optional[Media]:
        model = await self.session.get(MediaModel, media_id)
        if not model: return None
        return self._to_domain(model)

    async def get_by_entity(self, entity_type: str, entity_id: UUID) -> List[Media]:
        from sqlalchemy import select
        stmt = select(MediaModel).where(
            (MediaModel.entity_type == entity_type) &
            (MediaModel.entity_id == entity_id)
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, media_id: UUID) -> None:
        model = await self.session.get(MediaModel, media_id)
        if model: await self.session.delete(model)

    def _to_domain(self, model: MediaModel) -> Media:
        return Media(
            media_id=model.id,
            entity_type=MediaEntityType(model.entity_type),
            entity_id=model.entity_id,
            file_url=model.file_url,
            file_size=model.file_size,
            mime_type=model.mime_type,
            file_hash=model.file_hash,
            width=model.width,
            height=model.height,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
