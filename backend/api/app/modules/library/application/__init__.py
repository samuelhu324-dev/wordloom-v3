"""
Application Layer - Use Cases and Ports

Purpose:
- Orchestrate Domain logic with Infrastructure
- Define contracts (Ports) for external dependencies
- Implement business workflows (UseCases)

Structure:
- ports/: Port interfaces (Input Ports + Output Ports)
  - input.py: UseCase interfaces + Request/Response DTOs
  - output.py: Repository interface
- use_cases/: UseCase implementations
  - create_library.py: CreateLibraryUseCase
  - get_library.py: GetLibraryUseCase
  - delete_library.py: DeleteLibraryUseCase

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_5 (UseCase splitting) + step_6 (Input Ports)
- DDD_RULES.yaml: library.implementation_layers.application_layer
"""

from .ports import (
    ICreateLibraryUseCase,
    IGetLibraryUseCase,
    IDeleteLibraryUseCase,
    ILibraryRepository,
    CreateLibraryRequest,
    CreateLibraryResponse,
    GetLibraryRequest,
    GetLibraryResponse,
    DeleteLibraryRequest,
)

from .use_cases import (
    CreateLibraryUseCase,
    GetLibraryUseCase,
    DeleteLibraryUseCase,
)

__all__ = [
    # Input Ports (UseCase interfaces)
    "ICreateLibraryUseCase",
    "IGetLibraryUseCase",
    "IDeleteLibraryUseCase",
    # Output Ports (Repository interface)
    "ILibraryRepository",
    # Request/Response DTOs
    "CreateLibraryRequest",
    "CreateLibraryResponse",
    "GetLibraryRequest",
    "GetLibraryResponse",
    "DeleteLibraryRequest",
    # UseCase implementations
    "CreateLibraryUseCase",
    "GetLibraryUseCase",
    "DeleteLibraryUseCase",
]
