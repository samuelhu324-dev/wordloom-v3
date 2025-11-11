"""
Library Router - FastAPI routes for Library endpoints

Exposes Library operations via HTTP API:
- POST /libraries - Create Library
- GET /libraries/{library_id} - Get Library by ID
- GET /libraries/user/{user_id} - Get Library for user
- PUT /libraries/{library_id} - Update Library
- DELETE /libraries/{library_id} - Delete Library
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Optional

from domains.library.schemas import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryDetailResponse,
)
from domains.library.service import LibraryService
from domains.library.exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    LibraryDomainException,
)

router = APIRouter(
    prefix="/libraries",
    tags=["libraries"],
    responses={404: {"description": "Library not found"}},
)


async def get_library_service() -> LibraryService:
    """
    Dependency injection for LibraryService

    In production, this would:
    - Get database session from app context
    - Get repository instance
    - Create service instance
    """
    # TODO: Implement dependency injection from app context
    pass


@router.post("", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library(
    user_id: UUID,
    request: LibraryCreate,
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    """
    Create a new Library for user

    Args:
        user_id: ID of the user
        request: LibraryCreate schema

    Returns:
        Created Library

    Raises:
        409: If user already has a Library
        422: If validation fails
    """
    try:
        library = await service.create_library(
            user_id=user_id,
            name=request.name,
        )
        return LibraryResponse.from_orm(library)
    except LibraryAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get("/{library_id}", response_model=LibraryDetailResponse)
async def get_library(
    library_id: UUID,
    service: LibraryService = Depends(get_library_service),
) -> LibraryDetailResponse:
    """
    Get Library by ID

    Args:
        library_id: ID of the Library

    Returns:
        Library details

    Raises:
        404: If Library not found
    """
    try:
        library = await service.get_library(library_id)
        return LibraryDetailResponse.from_orm(library)
    except LibraryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/user/{user_id}", response_model=LibraryDetailResponse)
async def get_user_library(
    user_id: UUID,
    service: LibraryService = Depends(get_library_service),
) -> LibraryDetailResponse:
    """
    Get Library for a user (one per user)

    Args:
        user_id: ID of the user

    Returns:
        Library details

    Raises:
        404: If user has no Library
    """
    try:
        library = await service.get_user_library(user_id)
        return LibraryDetailResponse.from_orm(library)
    except LibraryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{library_id}", response_model=LibraryResponse)
async def update_library(
    library_id: UUID,
    request: LibraryUpdate,
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    """
    Update Library

    Args:
        library_id: ID of the Library
        request: LibraryUpdate schema

    Returns:
        Updated Library

    Raises:
        404: If Library not found
        422: If validation fails
    """
    try:
        # Only update fields that are provided
        if request.name:
            library = await service.rename_library(library_id, request.name)
        else:
            library = await service.get_library(library_id)

        return LibraryResponse.from_orm(library)
    except LibraryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(
    library_id: UUID,
    service: LibraryService = Depends(get_library_service),
) -> None:
    """
    Delete a Library

    Args:
        library_id: ID of the Library

    Raises:
        404: If Library not found
    """
    try:
        await service.delete_library(library_id)
    except LibraryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
