"""
Bookshelf Router - FastAPI routes for Bookshelf endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from domains.bookshelf.schemas import BookshelfCreate, BookshelfUpdate, BookshelfResponse
from domains.bookshelf.service import BookshelfService
from domains.bookshelf.exceptions import BookshelfNotFoundError

router = APIRouter(
    prefix="/libraries/{library_id}/bookshelves",
    tags=["bookshelves"],
)


async def get_bookshelf_service() -> BookshelfService:
    """Dependency injection for BookshelfService"""
    pass


@router.post("", response_model=BookshelfResponse, status_code=status.HTTP_201_CREATED)
async def create_bookshelf(
    library_id: UUID,
    request: BookshelfCreate,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Create a new Bookshelf"""
    try:
        bookshelf = await service.create_bookshelf(
            library_id=library_id,
            name=request.name,
            description=request.description,
        )
        return BookshelfResponse.from_orm(bookshelf)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=List[BookshelfResponse])
async def list_bookshelves(
    library_id: UUID,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> List[BookshelfResponse]:
    """List all Bookshelves in a Library"""
    bookshelves = await service.list_bookshelves(library_id)
    return [BookshelfResponse.from_orm(b) for b in bookshelves]


@router.get("/{bookshelf_id}", response_model=BookshelfResponse)
async def get_bookshelf(
    bookshelf_id: UUID,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Get a Bookshelf by ID"""
    try:
        bookshelf = await service.get_bookshelf(bookshelf_id)
        return BookshelfResponse.from_orm(bookshelf)
    except BookshelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{bookshelf_id}", response_model=BookshelfResponse)
async def update_bookshelf(
    bookshelf_id: UUID,
    request: BookshelfUpdate,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Update a Bookshelf"""
    try:
        if request.name:
            bookshelf = await service.rename_bookshelf(bookshelf_id, request.name)
        else:
            bookshelf = await service.get_bookshelf(bookshelf_id)
        return BookshelfResponse.from_orm(bookshelf)
    except BookshelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{bookshelf_id}/pin", response_model=BookshelfResponse)
async def pin_bookshelf(
    bookshelf_id: UUID,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> BookshelfResponse:
    """Pin a Bookshelf"""
    try:
        bookshelf = await service.pin_bookshelf(bookshelf_id)
        return BookshelfResponse.from_orm(bookshelf)
    except BookshelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{bookshelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookshelf(
    bookshelf_id: UUID,
    service: BookshelfService = Depends(get_bookshelf_service),
) -> None:
    """Delete a Bookshelf"""
    try:
        await service.delete_bookshelf(bookshelf_id)
    except BookshelfNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
