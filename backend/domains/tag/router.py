"""Tag Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from domains.tag.schemas import TagCreate, TagUpdate, TagResponse
from domains.tag.service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])

async def get_tag_service() -> TagService: pass

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(request: TagCreate, service: TagService = Depends(get_tag_service)):
    try:
        tag = await service.create_tag(request.name, request.color, request.icon, request.description)
        return TagResponse.from_orm(tag)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("", response_model=List[TagResponse])
async def list_tags(service: TagService = Depends(get_tag_service)):
    tags = await service.list_tags()
    return [TagResponse.from_orm(t) for t in tags]

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: UUID, service: TagService = Depends(get_tag_service)):
    try:
        tag = await service.get_tag(tag_id)
        return TagResponse.from_orm(tag)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: UUID, service: TagService = Depends(get_tag_service)):
    try:
        await service.delete_tag(tag_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
