"""Tag Repository"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domains.tag.domain import Tag, TagName, TagColor, TagIcon
from domains.tag.models import TagModel

class TagRepository(ABC):
    @abstractmethod
    async def save(self, tag: Tag) -> None: pass
    @abstractmethod
    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]: pass
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Tag]: pass
    @abstractmethod
    async def list_all(self) -> List[Tag]: pass
    @abstractmethod
    async def delete(self, tag_id: UUID) -> None: pass

class TagRepositoryImpl(TagRepository):
    def __init__(self, session):
        self.session = session

    async def save(self, tag: Tag) -> None:
        model = TagModel(
            id=tag.id,
            name=tag.name.value,
            color=tag.color.value,
            icon=tag.icon.value,
            description=tag.description,
            count=tag.count,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
        )
        self.session.add(model)

    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        model = await self.session.get(TagModel, tag_id)
        if not model: return None
        return self._to_domain(model)

    async def get_by_name(self, name: str) -> Optional[Tag]:
        from sqlalchemy import select
        stmt = select(TagModel).where(TagModel.name == name)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if not model: return None
        return self._to_domain(model)

    async def list_all(self) -> List[Tag]:
        from sqlalchemy import select
        stmt = select(TagModel).order_by(TagModel.count.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, tag_id: UUID) -> None:
        model = await self.session.get(TagModel, tag_id)
        if model: await self.session.delete(model)

    def _to_domain(self, model: TagModel) -> Tag:
        return Tag(
            tag_id=model.id,
            name=TagName(value=model.name),
            color=TagColor(value=model.color),
            icon=TagIcon(value=model.icon) if model.icon else TagIcon(),
            description=model.description,
            count=model.count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
