"""
Library 应用层 - Use Cases & Ports

应用层（Hexagonal 中间环）编排域逻辑。

结构:
  application/
  ├── ports/
  │   ├── input.py       - UseCase 接口（输入端口）
  │   └── output.py      - Repository 接口（输出端口）
  ├── use_cases/
  │   ├── get_user_library.py
  │   ├── create_library.py
  │   └── delete_library.py
  └── __init__.py

依赖流向:
  UseCase ← Repository (输出端口)
  Router → UseCase (输入端口)

RULE-001: 每个用户一个 Library（在 Use Case 中强制）
"""
