"""
Book 应用层 - Use Cases & Ports

应用层（Hexagonal 中间环）编排域逻辑。

结构:
  application/
  ├── ports/
  │   ├── input.py       - UseCase 接口（输入端口）
  │   └── output.py      - Repository 接口（输出端口）
  ├── use_cases/
  │   ├── create_book.py
  │   ├── list_books.py
  │   ├── get_book.py
  │   ├── update_book.py
  │   ├── delete_book.py
  │   ├── restore_book.py
  │   └── list_deleted_books.py
  └── __init__.py

依赖流向:
  UseCase ← Repository (输出端口)
  Router → UseCase (输入端口)

RULE-012: 软删除使用 soft_deleted_at 时间戳（在适配器中强制）
"""
