"""
Block Ports - 所有 Input 和 Output Port 接口

Output Ports (repository.py):
  - BlockRepository

Input Ports (input.py):
  - CreateBlockUseCase
  - ListBlocksUseCase
  - GetBlockUseCase
  - UpdateBlockUseCase
  - ReorderBlocksUseCase
  - DeleteBlockUseCase
  - RestoreBlockUseCase
  - ListDeletedBlocksUseCase

Request/Response DTOs:
  - CreateBlockRequest, BlockResponse
  - ListBlocksRequest
  - UpdateBlockRequest
  - ReorderBlocksRequest
  - ...
"""

# Output ports (repository)
from .output import BlockRepository

# Input ports (use cases) + DTOs
from .input import (
    CreateBlockUseCase,
    ListBlocksUseCase,
    GetBlockUseCase,
    UpdateBlockUseCase,
    ReorderBlocksUseCase,
    DeleteBlockUseCase,
    RestoreBlockUseCase,
    ListDeletedBlocksUseCase,
    # Request DTOs
    CreateBlockRequest,
    ListBlocksRequest,
    GetBlockRequest,
    UpdateBlockRequest,
    ReorderBlocksRequest,
    DeleteBlockRequest,
    RestoreBlockRequest,
    ListDeletedBlocksRequest,
    # Response DTOs
    BlockResponse,
    BlockListResponse,
)

__all__ = [
    # Output ports
    "BlockRepository",
    # Input ports
    "CreateBlockUseCase",
    "ListBlocksUseCase",
    "GetBlockUseCase",
    "UpdateBlockUseCase",
    "ReorderBlocksUseCase",
    "DeleteBlockUseCase",
    "RestoreBlockUseCase",
    "ListDeletedBlocksUseCase",
    # Request DTOs
    "CreateBlockRequest",
    "ListBlocksRequest",
    "GetBlockRequest",
    "UpdateBlockRequest",
    "ReorderBlocksRequest",
    "DeleteBlockRequest",
    "RestoreBlockRequest",
    "ListDeletedBlocksRequest",
    # Response DTOs
    "BlockResponse",
    "BlockListResponse",
]
