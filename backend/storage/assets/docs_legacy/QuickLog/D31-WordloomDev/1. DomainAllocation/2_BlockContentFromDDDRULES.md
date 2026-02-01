1. 现在该设计所有 BlockType 吗？
答案：不用。现在只保留通用 BlockContent，以后慢慢调整。

维度	说明
业务阶段	你现在还在 Phase 1（基础设施），还没进 Phase 3（业务政策）
不确定性	代码、表格、检查点等具体需求还没完全明确
成本	现在设计完整的多态体系，之后改需求反而更麻烦
YAGNI 原则	"You Aren't Gonna Need It" - 不过度设计

保持简单，打好地基：
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class BlockContent(ValueObject):
    """
    Value object for Block content

    当前阶段：统一的字符串存储 + 通用元数据
    TODO: Phase 3 时按 block_type 细分为多个专用类
    """
    value: str  # 实际内容
    metadata: Dict[str, Any] | None = None  # 灵活扩展

    def __post_init__(self):
        if len(self.value) > 10000:
            raise ValueError("Block content cannot exceed 10000 characters")
```

为什么这样做：

✅ 能承载所有现有 type（text/code/image reference/等）
✅ metadata 字段可灵活存储 type 特定数据
✅ 不过度设计，保持简洁
✅ 以后要细分时，只需新增子类就行

现在 (Phase 1)          未来 (Phase 3)
┌─────────────────┐    ┌──────────────────┐
│ BlockContent    │    │ BlockContent     │
│  value: str     │    │ (abstract base)  │
│  metadata: {}   │    │                  │
└─────────────────┘    ├─ TextContent    │
                        ├─ CodeContent    │
                        ├─ ImageContent   │
                        └─ ...etc         │
                        └──────────────────┘

2. BlockContent 是"已经出现的文本框"还是"BlockManager 插入的"？
答案：都不是。BlockContent 是数据层，UI 是另一回事。
┌─────────────────────────────────────────────────────────┐
│ 表现层 (Frontend / UI)                                   │
│ - React TextEditor 组件                                  │
│ - 实时编辑交互                                           │
│ - 光标、选择、格式化按钮                                 │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP POST /api/blocks
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 应用层 (API Router)                                      │
│ - 接收 { content: "...", type: "text" }                │
│ - 调用 BlockService.create_block()                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 领域层 (DDD Domain)  ← 你现在在这里！                   │
│ - Block Aggregate                                       │
│ - BlockContent Value Object                            │
│ - BlockCreatedEvent 事件                               │
│ - 业务规则验证                                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 存储层 (Persistence)                                    │
│ - 存入数据库                                             │
│ - Block 表、Content 表                                 │
└─────────────────────────────────────────────────────────┘

具体对应关系
你现在定义的 BlockContent 是：
```python
@dataclass(frozen=True)
class BlockContent(ValueObject):
    value: str       # ← 这是存储的内容（纯数据）
    metadata: {}     # ← 这是元数据（纯数据）
```

```python
这是"数据对象"，不是"UI 组件"。
用户在 Word 里打字
    ↓
Frontend TextEditor onChange 事件
    ↓
发送 HTTP POST:
{
  "book_id": "xxx",
  "block_type": "text",
  "content": "用户输入的文本",
  "metadata": { "language": "markdown" }
}
    ↓
Backend BlockService.create_block()
    ↓
创建 BlockContent ValueObject:
  BlockContent(
    value="用户输入的文本",
    metadata={"language": "markdown"}
  )
    ↓
创建 Block Aggregate:
  Block(
    id=uuid4(),
    book_id="xxx",
    type=BlockType.TEXT,
    content=BlockContent(...),
    ...
  )
    ↓
保存到数据库
```

BlockManager 是什么关系？
如果你有 BlockManager 这样的东西：
```python
class BlockManager:
    def insert_block(self, book_id, block_type, content):
        # 这是"应用服务层"的概念
        # 调用领域逻辑来创建 Block
        block = Block.create_xxx_block(...)  # 使用工厂方法
        self.block_repo.save(block)
```

```python
UI 点击"插入文本框"
    ↓
BlockManager.insert_block(type="text", ...)
    ↓
创建 BlockContent + Block
    ↓
数据库存储
```

但 BlockContent 本身还是纯数据对象，不是"文本框"。

BlockContent 的唯一职责
是验证和封装内容数据，不管：

❌ 怎么输入（UI 组件、API、CLI）
❌ 怎么显示（Markdown、富文本、代码高亮）
❌ 用户体验（光标位置、撤销历史）


