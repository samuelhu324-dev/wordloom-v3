"""FastAPI routes exposing Basement workflows."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.app.dependencies import DIContainer, get_di_container
from api.app.modules.book.exceptions import (
    BookException,
    BookOperationError,
)

from ..application.dtos import (
    HardDeleteBookCommand,
    ListBasementBooksQuery,
    MoveBookToBasementCommand,
    RestoreBookFromBasementCommand,
)
from ..application.use_cases.hard_delete_book import HardDeleteBookUseCase
from ..application.use_cases.list_basement_books import ListBasementBooksUseCase
from ..application.use_cases.move_book_to_basement import MoveBookToBasementUseCase
from ..application.use_cases.restore_book_from_basement import RestoreBookFromBasementUseCase
from ..domain.entities import BasementBookSnapshot
from ..schemas import (
    BasementBookListResponse,
    BasementBookResponse,
    MoveBookToBasementRequest,
    RestoreBookFromBasementRequest,
)

router = APIRouter(prefix="/admin", tags=["Basement"])


@router.post(
    "/books/{book_id}/move-to-basement",
    response_model=BasementBookResponse,
    status_code=status.HTTP_200_OK,
)
async def move_book_to_basement(
    book_id: UUID,
    payload: MoveBookToBasementRequest,
    di: Annotated[DIContainer, Depends(get_di_container)],
):
    use_case: MoveBookToBasementUseCase = di.get_move_book_to_basement_use_case()
    command = MoveBookToBasementCommand(
        book_id=book_id,
        basement_bookshelf_id=payload.basement_bookshelf_id,
        reason=payload.reason,
    )
    try:
        snapshot = await use_case.execute(command)
        return _snapshot_to_response(snapshot)
    except BookException as exc:
        raise HTTPException(status_code=exc.http_status_code, detail=exc.to_dict()) from exc


@router.post(
    "/books/{book_id}/restore-from-basement",
    response_model=BasementBookResponse,
    status_code=status.HTTP_200_OK,
)
async def restore_book_from_basement(
    book_id: UUID,
    payload: RestoreBookFromBasementRequest,
    di: Annotated[DIContainer, Depends(get_di_container)],
):
    use_case: RestoreBookFromBasementUseCase = di.get_restore_book_from_basement_use_case()
    command = RestoreBookFromBasementCommand(
        book_id=book_id,
        target_bookshelf_id=payload.target_bookshelf_id,
    )
    try:
        snapshot = await use_case.execute(command)
        return _snapshot_to_response(snapshot)
    except BookException as exc:
        raise HTTPException(status_code=exc.http_status_code, detail=exc.to_dict()) from exc


@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def hard_delete_book(
    book_id: UUID,
    di: Annotated[DIContainer, Depends(get_di_container)],
):
    use_case: HardDeleteBookUseCase = di.get_hard_delete_book_use_case()
    command = HardDeleteBookCommand(book_id=book_id)
    try:
        await use_case.execute(command)
    except BookException as exc:
        raise HTTPException(status_code=exc.http_status_code, detail=exc.to_dict()) from exc


@router.get(
    "/libraries/{library_id}/basement/books",
    response_model=BasementBookListResponse,
)
async def list_basement_books(
    library_id: UUID,
    di: Annotated[DIContainer, Depends(get_di_container)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    use_case: ListBasementBooksUseCase = di.get_list_basement_books_use_case()
    query = ListBasementBooksQuery(library_id=library_id, skip=skip, limit=limit)
    try:
        snapshots, total = await use_case.execute(query)
    except BookOperationError as exc:
        raise HTTPException(status_code=exc.http_status_code, detail=exc.to_dict()) from exc

    items = [_snapshot_to_response(snapshot) for snapshot in snapshots]
    has_more = skip + len(items) < total
    page = (skip // limit) + 1 if limit else 1
    return BasementBookListResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        has_more=has_more,
    )


def _snapshot_to_response(snapshot: BasementBookSnapshot) -> BasementBookResponse:
    return BasementBookResponse(
        id=snapshot.id,
        library_id=snapshot.library_id,
        bookshelf_id=snapshot.bookshelf_id,
        previous_bookshelf_id=snapshot.previous_bookshelf_id,
        title=snapshot.title,
        summary=snapshot.summary,
        status=snapshot.status,
        block_count=snapshot.block_count,
        moved_to_basement_at=snapshot.moved_to_basement_at,
        soft_deleted_at=snapshot.soft_deleted_at,
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
    )
