"""
Library Domain Module

Public API exports for the Library aggregate root and related components.

Hexagonal Architecture:
  - Domain: library, library_name (from .domain)
  - Application: UseCase interfaces (from .application)
  - Persistence: ORM models (from infra.database.models)
  - HTTP: Router (from .routers)
"""

from .domain import Library, LibraryName
from .application.ports.input import (
    ICreateLibraryUseCase,
    IGetLibraryUseCase,
    IDeleteLibraryUseCase,
)
from .application.use_cases.create_library import CreateLibraryUseCase
from .application.use_cases.get_library import GetLibraryUseCase
from .application.use_cases.delete_library import DeleteLibraryUseCase
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
# from .routers.library_router import router  # Commented out to avoid circular imports in testing

# ORM Models (from infra layer)
# Note: Don't import here - use: from infra.database.models.library_models import LibraryModel

__all__ = [
    # Domain
    "Library",
    "LibraryName",

    # Application - Port Interfaces
    "ICreateLibraryUseCase",
    "IGetLibraryUseCase",
    "IDeleteLibraryUseCase",

    # Application - UseCase Implementations
    "CreateLibraryUseCase",
    "GetLibraryUseCase",
    "DeleteLibraryUseCase",

    # API Schemas
    "LibraryCreate",
    "LibraryUpdate",
    "LibraryResponse",
    "LibraryDetailResponse",

    # Domain Exceptions
    "LibraryNotFoundError",
    "LibraryAlreadyExistsError",
    "InvalidLibraryNameError",
    "LibraryUserAssociationError",

    # HTTP Router (commented out to avoid circular imports)
    # "router",
]
