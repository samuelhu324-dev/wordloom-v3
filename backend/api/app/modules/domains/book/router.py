"""Book Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from domains.book.schemas import BookCreate, BookUpdate, BookResponse
from domains.book.service import BookService

router = APIRouter(prefix="/bookshelves/{bookshelf_id}/books", tags=["books"])

async def get_book_service() -> BookService: pass

@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(bookshelf_id: UUID, request: BookCreate, service: BookService = Depends(get_book_service)):
    try:
        book = await service.create_book(bookshelf_id, request.title, request.summary)
        return BookResponse.from_orm(book)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("", response_model=List[BookResponse])
async def list_books(bookshelf_id: UUID, service: BookService = Depends(get_book_service)):
    books = await service.list_books(bookshelf_id)
    return [BookResponse.from_orm(b) for b in books]

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, service: BookService = Depends(get_book_service)):
    try:
        book = await service.get_book(book_id)
        return BookResponse.from_orm(book)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: UUID, service: BookService = Depends(get_book_service)):
    try:
        await service.delete_book(book_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
