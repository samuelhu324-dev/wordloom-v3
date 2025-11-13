"""
Block UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类：
  - create_block.py        - CreateBlockUseCase
  - list_blocks.py         - ListBlocksUseCase
  - get_block.py           - GetBlockUseCase
  - update_block.py        - UpdateBlockUseCase
  - reorder_blocks.py      - ReorderBlocksUseCase
  - delete_block.py        - DeleteBlockUseCase
  - restore_block.py       - RestoreBlockUseCase
  - list_deleted_blocks.py - ListDeletedBlocksUseCase

Block 类型: TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE
排序: 使用分数索引（Fractional Index）实现 O(1) 插入/移动
软删除: 通过 soft_deleted_at 时间戳
"""

from .create_block import CreateBlockUseCase
from .list_blocks import ListBlocksUseCase
from .get_block import GetBlockUseCase
from .update_block import UpdateBlockUseCase
from .reorder_blocks import ReorderBlocksUseCase
from .delete_block import DeleteBlockUseCase
from .restore_block import RestoreBlockUseCase
from .list_deleted_blocks import ListDeletedBlocksUseCase

__all__ = [
    "CreateBlockUseCase",
    "ListBlocksUseCase",
    "GetBlockUseCase",
    "UpdateBlockUseCase",
    "ReorderBlocksUseCase",
    "DeleteBlockUseCase",
    "RestoreBlockUseCase",
    "ListDeletedBlocksUseCase",
]
