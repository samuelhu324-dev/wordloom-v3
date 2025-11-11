"""Tag Service"""
from typing import List
from uuid import UUID
from domains.tag.domain import Tag
from domains.tag.repository import TagRepository

class TagService:
    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def create_tag(self, name: str, color: str = None, icon: str = None, description: str = None) -> Tag:
        tag = Tag.create(name, color, icon, description)
        await self.repository.save(tag)
        return tag

    async def get_tag(self, tag_id: UUID) -> Tag:
        tag = await self.repository.get_by_id(tag_id)
        if not tag: raise Exception(f"Tag {tag_id} not found")
        return tag

    async def list_tags(self) -> List[Tag]:
        return await self.repository.list_all()

    async def rename_tag(self, tag_id: UUID, new_name: str) -> Tag:
        tag = await self.get_tag(tag_id)
        tag.rename(new_name)
        await self.repository.save(tag)
        return tag

    async def delete_tag(self, tag_id: UUID) -> None:
        tag = await self.get_tag(tag_id)
        tag.mark_deleted()
        await self.repository.save(tag)
        await self.repository.delete(tag_id)
