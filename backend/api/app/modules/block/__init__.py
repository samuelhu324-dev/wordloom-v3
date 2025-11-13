"""
Block Domain Module

Public API exports for the Block value object and related components.
"""

from .domain import Block, BlockType, BlockContent
from .service import BlockService
from .repository import BlockRepository, BlockRepositoryImpl
from .models import BlockModel
from .schemas import (
    BlockCreate,
    BlockUpdate,
    BlockResponse,
    BlockDetailResponse,
)
from .exceptions import (
    BlockNotFoundError,
    InvalidBlockTypeError,
    InvalidBlockContentError,
    InvalidHeadingLevelError,
    BlockOperationError,
)
from .router import router

__all__ = [
    "Block",
    "BlockType",
    "BlockContent",
    "BlockService",
    "BlockRepository",
    "BlockRepositoryImpl",
    "BlockModel",
    "BlockCreate",
    "BlockUpdate",
    "BlockResponse",
    "BlockDetailResponse",
    "BlockNotFoundError",
    "InvalidBlockTypeError",
    "InvalidBlockContentError",
    "InvalidHeadingLevelError",
    "BlockOperationError",
    "router",
]
