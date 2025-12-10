"""
Block Domain Layer - Public API

Exports:
- Block: Aggregate Root
- BlockType: Enumeration of block types
- BlockContent: Value Object for content validation
- Domain Events: BlockCreated, BlockUpdated, BlockReordered, BlockDeleted, BlockRestored
"""

from .block import Block, BlockType, BlockContent
from .events import (
    BlockCreated,
    BlockUpdated,
    BlockReordered,
    BlockDeleted,
    BlockRestored,
)

__all__ = [
    "Block",
    "BlockType",
    "BlockContent",
    "BlockCreated",
    "BlockUpdated",
    "BlockReordered",
    "BlockDeleted",
    "BlockRestored",
]
