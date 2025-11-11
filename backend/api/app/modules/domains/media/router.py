"""Media Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from domains.media.schemas import MediaCreate, MediaResponse
from domains.media.service import MediaService

router = APIRouter(prefix="/media", tags=["media"])

async def get_media_service() -> MediaService: pass

@router.post("", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(request: MediaCreate, service: MediaService = Depends(get_media_service)):
    try:
        media = await service.upload_media(request.entity_type, request.entity_id, request.file_url, request.file_size, request.mime_type, request.file_hash, request.width, request.height)
        return MediaResponse.from_orm(media)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(media_id: UUID, service: MediaService = Depends(get_media_service)):
    try:
        media = await service.get_media(media_id)
        return MediaResponse.from_orm(media)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/entity/{entity_type}/{entity_id}", response_model=List[MediaResponse])
async def get_entity_media(entity_type: str, entity_id: UUID, service: MediaService = Depends(get_media_service)):
    media_list = await service.get_entity_media(entity_type, entity_id)
    return [MediaResponse.from_orm(m) for m in media_list]

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: UUID, service: MediaService = Depends(get_media_service)):
    try:
        await service.delete_media(media_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
