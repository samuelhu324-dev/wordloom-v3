"""
Book UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类：
  - create_book.py         - CreateBookUseCase
  - list_books.py          - ListBooksUseCase
  - get_book.py            - GetBookUseCase
  - update_book.py         - UpdateBookUseCase
  - delete_book.py         - DeleteBookUseCase
  - restore_book.py        - RestoreBookUseCase
  - list_deleted_books.py  - ListDeletedBooksUseCase

RULE-012: 书籍支持软删除，通过 soft_deleted_at 时间戳
"""

from .create_book import CreateBookUseCase
from .list_books import ListBooksUseCase
from .get_book import GetBookUseCase
from .update_book import UpdateBookUseCase
from .delete_book import DeleteBookUseCase
from .restore_book import RestoreBookUseCase
from .list_deleted_books import ListDeletedBooksUseCase

__all__ = [
    "CreateBookUseCase",
    "ListBooksUseCase",
    "GetBookUseCase",
    "UpdateBookUseCase",
    "DeleteBookUseCase",
    "RestoreBookUseCase",
    "ListDeletedBooksUseCase",
]
