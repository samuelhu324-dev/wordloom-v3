# Library Router - FastAPI routes for Library endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

# Application layer imports
from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
from api.app.modules.library.application.use_cases.delete_library import DeleteLibraryUseCase
from api.app.modules.library.application.ports.input import (
    CreateLibraryRequest,
    CreateLibraryResponse,
    GetLibraryRequest,
    GetLibraryResponse,
    DeleteLibraryRequest,
)

# Infrastructure imports
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.database import get_db_session

# Domain exceptions
from api.app.modules.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    InvalidLibraryNameError,
    LibraryException,
    DomainException,
)

# Schemas
from api.app.modules.library.schemas import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryDetailResponse,
    ErrorDetail,
)

# Security
from api.app.config.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/libraries",
    tags=["libraries"],
    responses={
        404: {"description": "Library not found", "model": ErrorDetail},
        409: {"description": "Conflict", "model": ErrorDetail},
        422: {"description": "Validation error", "model": ErrorDetail},
    },
)

async def get_create_library_usecase(session: AsyncSession = Depends(get_db_session)) -> CreateLibraryUseCase:
    repository = SQLAlchemyLibraryRepository(session)
    return CreateLibraryUseCase(repository=repository)

async def get_get_library_usecase(session: AsyncSession = Depends(get_db_session)) -> GetLibraryUseCase:
    repository = SQLAlchemyLibraryRepository(session)
    return GetLibraryUseCase(repository=repository)

async def get_delete_library_usecase(session: AsyncSession = Depends(get_db_session)) -> DeleteLibraryUseCase:
    repository = SQLAlchemyLibraryRepository(session)
    return DeleteLibraryUseCase(repository=repository)

def _handle_domain_exception(exc: DomainException) -> HTTPException:
    error_detail = exc.to_dict() if hasattr(exc, "to_dict") else {"message": str(exc)}
    return HTTPException(
        status_code=exc.http_status if hasattr(exc, "http_status") else 500,
        detail=error_detail,
    )

@router.post("", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library(
    request: LibraryCreate,
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateLibraryUseCase = Depends(get_create_library_usecase),
) -> LibraryResponse:
    try:
        uc_request = CreateLibraryRequest(user_id=user_id, name=request.name)
        uc_response = await use_case.execute(uc_request)
        return LibraryResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            created_at=uc_response.created_at,
            updated_at=uc_response.updated_at,
        )
    except (LibraryAlreadyExistsError, InvalidLibraryNameError, LibraryException) as exc:
        raise _handle_domain_exception(exc)

@router.get("/{library_id}", response_model=LibraryDetailResponse)
async def get_library(
    library_id: UUID = Path(...),
    use_case: GetLibraryUseCase = Depends(get_get_library_usecase),
) -> LibraryDetailResponse:
    try:
        uc_request = GetLibraryRequest(library_id=library_id)
        uc_response = await use_case.execute(uc_request)
        return LibraryDetailResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            created_at=uc_response.created_at,
            updated_at=uc_response.updated_at,
            bookshelf_count=0,
            basement_bookshelf_id=uc_response.basement_bookshelf_id,
            status="active",
        )
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.get("/user/{user_id}", response_model=LibraryDetailResponse)
async def get_user_library(
    user_id: UUID = Path(...),
    use_case: GetLibraryUseCase = Depends(get_get_library_usecase),
) -> LibraryDetailResponse:
    try:
        uc_request = GetLibraryRequest(user_id=user_id)
        uc_response = await use_case.execute(uc_request)
        return LibraryDetailResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            created_at=uc_response.created_at,
            updated_at=uc_response.updated_at,
            bookshelf_count=0,
            basement_bookshelf_id=uc_response.basement_bookshelf_id,
            status="active",
        )
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.put("/{library_id}", response_model=LibraryResponse)
async def update_library(
    library_id: UUID = Path(...),
    request: LibraryUpdate = None,
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetLibraryUseCase = Depends(get_get_library_usecase),
) -> LibraryResponse:
    try:
        uc_request = GetLibraryRequest(library_id=library_id)
        uc_response = await use_case.execute(uc_request)
        if uc_response.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return LibraryResponse(
            id=uc_response.library_id,
            user_id=uc_response.user_id,
            name=uc_response.name,
            created_at=uc_response.created_at,
            updated_at=uc_response.updated_at,
        )
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(
    library_id: UUID = Path(...),
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeleteLibraryUseCase = Depends(get_delete_library_usecase),
) -> None:
    try:
        uc_request = DeleteLibraryRequest(library_id=library_id)
        await use_case.execute(uc_request)
    except LibraryException as exc:
        raise _handle_domain_exception(exc)

@router.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "library"}

