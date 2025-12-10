"""
Book UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类：
  - create_book.py         - CreateBookUseCase
  - list_books.py          - ListBooksUseCase
  - get_book.py            - GetBookUseCase
  - update_book.py         - UpdateBookUseCase
  - delete_book.py         - DeleteBookUseCase
  - restore_book.py        - RestoreBookUseCase
  - move_book.py           - MoveBookUseCase (RULE-011)
  - list_deleted_books.py  - ListDeletedBooksUseCase (RULE-012)

RULE-011: 书籍可以跨 Bookshelf 转移
RULE-012: 书籍支持软删除到 Basement，通过 soft_deleted_at 时间戳
"""

from .create_book import CreateBookUseCase
from .list_books import ListBooksUseCase
from .get_book import GetBookUseCase
from .update_book import UpdateBookUseCase
from .delete_book import DeleteBookUseCase
from .restore_book import RestoreBookUseCase
from .move_book import MoveBookUseCase
from .list_deleted_books import ListDeletedBooksUseCase
from .recalculate_book_maturity import RecalculateBookMaturityUseCase
from .update_book_maturity import UpdateBookMaturityUseCase

__all__ = [
    "CreateBookUseCase",
    "ListBooksUseCase",
    "GetBookUseCase",
    "UpdateBookUseCase",
    "DeleteBookUseCase",
    "RestoreBookUseCase",
    "MoveBookUseCase",
    "ListDeletedBooksUseCase",
    "RecalculateBookMaturityUseCase",
    "UpdateBookMaturityUseCase",
]
