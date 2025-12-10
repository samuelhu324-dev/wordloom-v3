"""
Block 应用层 - Use Cases & Ports

应用层（Hexagonal 中间环）编排域逻辑。

结构:
  application/
  ├── ports/
  │   ├── input.py       - UseCase 接口（输入端口）
  │   └── output.py      - Repository 接口（输出端口）
  ├── use_cases/
  │   ├── create_block.py
  │   ├── list_blocks.py
  │   ├── get_block.py
  │   ├── update_block.py
  │   ├── reorder_blocks.py
  │   ├── delete_block.py
  │   ├── restore_block.py
  │   └── list_deleted_blocks.py
  └── __init__.py

依赖流向:
  UseCase ← Repository (输出端口)
  Router → UseCase (输入端口)

Block 类型: TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE
排序: 分数索引（Decimal 字段）用于 O(1) 插入
软删除: soft_deleted_at 时间戳
"""
