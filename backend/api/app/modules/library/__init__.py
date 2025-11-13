"""
Library Domain Module

Public API exports for the Library aggregate root and related components.
"""

from .domain import Library, LibraryName
from .service import LibraryService
from .repository import LibraryRepository, LibraryRepositoryImpl
from .models import LibraryModel
from .schemas import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryDetailResponse,
)
from .exceptions import (
    LibraryNotFoundError,
    LibraryAlreadyExistsError,
    InvalidLibraryNameError,
    LibraryUserAssociationError,
)
from .router import router

__all__ = [
    "Library",
    "LibraryName",
    "LibraryService",
    "LibraryRepository",
    "LibraryRepositoryImpl",
    "LibraryModel",
    "LibraryCreate",
    "LibraryUpdate",
    "LibraryResponse",
    "LibraryDetailResponse",
    "LibraryNotFoundError",
    "LibraryAlreadyExistsError",
    "InvalidLibraryNameError",
    "LibraryUserAssociationError",
    "router",
]
