"""Block Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from domains.block.schemas import BlockCreate, BlockUpdate, BlockResponse
from domains.block.service import BlockService

router = APIRouter(prefix="/books/{book_id}/blocks", tags=["blocks"])

async def get_block_service() -> BlockService: pass

@router.post("", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(book_id: UUID, request: BlockCreate, service: BlockService = Depends(get_block_service)):
    try:
        block = await service.create_block(book_id, request.block_type, request.content, request.order)
        return BlockResponse.from_orm(block)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("", response_model=List[BlockResponse])
async def list_blocks(book_id: UUID, service: BlockService = Depends(get_block_service)):
    blocks = await service.list_blocks(book_id)
    return [BlockResponse.from_orm(b) for b in blocks]

@router.get("/{block_id}", response_model=BlockResponse)
async def get_block(block_id: UUID, service: BlockService = Depends(get_block_service)):
    try:
        block = await service.get_block(block_id)
        return BlockResponse.from_orm(block)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(block_id: UUID, service: BlockService = Depends(get_block_service)):
    try:
        await service.delete_block(block_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
