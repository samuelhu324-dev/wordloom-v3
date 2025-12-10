"""
Bookshelf 应用层 - Use Cases & Ports

应用层（Hexagonal 中间环）编排域逻辑。

结构:
  application/
  ├── ports/
  │   ├── input.py       - UseCase 接口（输入端口）
  │   └── output.py      - Repository 接口（输出端口）
  ├── use_cases/
  │   ├── create_bookshelf.py
  │   ├── list_bookshelves.py
  │   ├── get_bookshelf.py
  │   ├── update_bookshelf.py
  │   ├── delete_bookshelf.py
  │   └── get_basement.py
  └── __init__.py

依赖流向:
  UseCase ← Repository (输出端口)
  Router → UseCase (输入端口)

RULE-006: 每个 Library 内名字唯一（在 Use Case 中强制）
RULE-010: Basement 特殊书架（每个 Library 创建，不能删除）
"""
