"""FastAPI router for the maturity module."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from api.app.dependencies import DIContainer, get_di_container
from ..application.dtos import CalculateBookMaturityCommand, GetSnapshotsQuery
from ..schemas import MaturitySnapshotSchema

router = APIRouter(prefix="/maturity/books", tags=["Maturity"])


@router.post("/{book_id}/evaluate", response_model=MaturitySnapshotSchema)
async def evaluate_book_maturity(
    book_id: UUID,
    di: Annotated[DIContainer, Depends(get_di_container)],
):
    use_case = di.get_calculate_book_maturity_use_case()
    result = await use_case.execute(CalculateBookMaturityCommand(book_id=book_id))
    return MaturitySnapshotSchema.from_domain(result.snapshot)


@router.get("/{book_id}/snapshots", response_model=list[MaturitySnapshotSchema])
async def list_book_maturity_snapshots(
    book_id: UUID,
    di: Annotated[DIContainer, Depends(get_di_container)],
    limit: int = 10,
):
    use_case = di.get_list_maturity_snapshots_use_case()
    result = await use_case.execute(GetSnapshotsQuery(book_id=book_id, limit=limit))
    return [MaturitySnapshotSchema.from_domain(snapshot) for snapshot in result.snapshots]
