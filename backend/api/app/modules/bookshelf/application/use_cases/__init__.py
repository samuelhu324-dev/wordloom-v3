"""
Bookshelf UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类：
  - create_bookshelf.py   - CreateBookshelfUseCase
  - list_bookshelves.py   - ListBookshelvesUseCase
  - get_bookshelf.py      - GetBookshelfUseCase
  - update_bookshelf.py   - UpdateBookshelfUseCase
  - delete_bookshelf.py   - DeleteBookshelfUseCase
  - get_basement.py       - GetBasementUseCase

RULE-006: Bookshelf 名称在每个 Library 内唯一
RULE-010: Basement 是每个 Library 自动创建的特殊书架，不能删除
"""

from .create_bookshelf import CreateBookshelfUseCase
from .list_bookshelves import ListBookshelvesUseCase
from .get_bookshelf import GetBookshelfUseCase
from .update_bookshelf import UpdateBookshelfUseCase
from .delete_bookshelf import DeleteBookshelfUseCase
from .get_basement import GetBasementUseCase

__all__ = [
    "CreateBookshelfUseCase",
    "ListBookshelvesUseCase",
    "GetBookshelfUseCase",
    "UpdateBookshelfUseCase",
    "DeleteBookshelfUseCase",
    "GetBasementUseCase",
]
