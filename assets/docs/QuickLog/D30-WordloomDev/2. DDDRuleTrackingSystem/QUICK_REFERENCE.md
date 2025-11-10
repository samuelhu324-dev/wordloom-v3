# Wordloom v3 快速参考指南

**这是一份速查表，用于快速理解新架构。**

---

## 老架构 → v3 数据模型映射

| 老架构（Orbit） | v3 新架构 | 变化 |
|---|---|---|
| OrbitBookshelf | Bookshelf | 改为属于 Library（新增层级） |
| OrbitNote | Book | 重命名 |
| OrbitNote.blocks_json | Block | 扁平化为独立表 |
| OrbitTag | Tag | 保持全局标签 |
| OrbitNoteCheckpoint | Chronicle.Session | 移动到独立模块 |
| OrbitNoteCheckpointMarker | Chronicle.TimeSegment | 重命名 |
| OrbitMediaResource | MediaResource | 扩展 entity_type |
| (不存在) | Library | 新增（用户容器） |
| (不存在) | Chronicle | 新增（时间追踪） |

---

## 核心约束速记

### Library（1 条关键规则）
- ✅ **每个 User 只有 1 个 Library**（不可创建多个）

### Bookshelf（4 条关键规则）
- ✅ 可无限创建
- ✅ 必须属于 Library（FK: library_id）
- ✅ 支持优先级、紧急度、标签
- ✅ 删除时可级联删除或孤立处理

### Book（4 条关键规则）
- ✅ 可无限创建
- ✅ 必须属于 Bookshelf（FK: bookshelf_id）
- ✅ 包含有序 Blocks
- ✅ 支持复制

### Block（5 条关键规则）
- ✅ 可无限创建
- ✅ 必须有 type（text|code|image|checkpoint|translation|...）
- ✅ 有序排列（order 字段）
- ✅ 支持 metadata（type 特定的字段）
- ✅ 删除时清理关联媒体

### Tag（3 条关键规则）
- ✅ 全局唯一（name unique）
- ✅ 与 Book 多对多关联
- ✅ 支持颜色、图标、描述

### Chronicle（3 条关键规则）
- ✅ Session 必须有 started_at
- ✅ TimeSegment 时间范围有效
- ✅ Session 可选关联 Book

---

## 关键文件位置

### DDD 规则文档
```
backend/docs/DDD_RULES.yaml        ← 所有规则定义（25条不变量+14条政策）
```

### Domain 分析报告
```
DOMAIN_ANALYSIS.md                 ← 6000+ 字的详细分析
IMPLEMENTATION_GUIDE.md            ← 实现指南（7个部分）
```

### 后端模块位置
```
backend/api/app/modules/
├─ library/           ← 顶层容器
├─ bookshelf/         ← 第一级分类
├─ book/              ← 内容容器
├─ block/             ← 最小单位
├─ tag/               ← 全局标签
├─ media/             ← 媒体管理
├─ chronicle/         ← 时间追踪（新）
├─ search/            ← 搜索
├─ stats/             ← 统计
├─ theme/             ← 主题
└─ auth/              ← 认证
```

---

## 快速实现清单

### Phase 1：Domain 层（优先级）
- [ ] Library Domain
- [ ] Bookshelf Domain
- [ ] Book Domain
- [ ] Block Domain
- [ ] Tag Domain

**时间估计**：1 周

### Phase 2：Repository + Service
- [ ] 所有 Domain 的 Repository 实现
- [ ] 所有 Domain 的 Service 业务逻辑
- [ ] 集成测试（特别是级联删除）

**时间估计**：1 周

### Phase 3：API Routers
- [ ] 所有 Domain 的 Router 实现
- [ ] API 测试

**时间估计**：3-5 天

### Phase 4：迁移脚本
- [ ] 从 OrbitBookshelf → Bookshelf
- [ ] 从 OrbitNote → Book + Block
- [ ] 数据验证

**时间估计**：1 周

### Phase 5：Chronicle 模块（可选先做）
- [ ] Session + TimeSegment 实体
- [ ] 与 Wordloom 日记集成

**时间估计**：1 周

---

## 每个 Module 的文件结构

```
backend/api/app/modules/library/
├─ __init__.py             # 空或导出公共接口
├─ domain.py               # ⭐ AggregateRoot 定义（核心）
├─ models.py               # ORM Model（SQLAlchemy）
├─ schemas.py              # Pydantic Schema
├─ repository.py           # Repository 接口
├─ service.py              # Business Logic Service
├─ router.py               # FastAPI Router
└─ tests/
   ├─ __init__.py
   ├─ test_domain.py       # Unit tests for domain
   ├─ test_service.py      # Unit tests for service
   └─ test_integration.py  # Integration tests
```

---

## 从老架构提取的关键操作

### Bookshelf 操作（来自 BookshelfService）
- ✅ create_bookshelf()
- ✅ list_bookshelves()
- ✅ update_bookshelf()
- ✅ delete_bookshelf(cascade="orphan"|"delete")
- ✅ move_note_to_bookshelf()（→ move_book_to_bookshelf()）
- ✅ get_bookshelf_notes()（→ get_bookshelf_books()）
- ✅ increment_usage_count()

### Book 操作（来自 NoteService）
- ✅ duplicate_book()（核心操作）
- ✅ get_book_by_id()
- ✅ delete_book()
- ✅ _copy_book_uploads()（复制媒体文件）

---

## Block 类型参考

```python
# 支持的 Block 类型
BLOCK_TYPES = [
    "text",           # 纯文本
    "code",           # 代码块
    "image",          # 图片
    "table",          # 表格
    "list",           # 列表
    "quote",          # 引用
    "checkpoint",     # 检查点（从老 Checkpoint 迁移）
    "translation",    # 翻译（未来功能，可嵌套）
    "media",          # 通用媒体
    "embed",          # 嵌入内容
]

# 每个 Block 的结构
class Block:
    id: UUID
    book_id: UUID
    type: str                 # 上面的类型之一
    content: str              # 主要内容
    metadata: Dict[str, Any]  # 类型特定的字段
    order: int                # 排序位置
    created_at: datetime
    updated_at: datetime
```

---

## Checkpoint 的两重身份

### 1. 作为 Block 类型（在 Book 内）
```python
Book
  └─ blocks: [
      Block { type: "checkpoint", content: "第一章完成", metadata: {...} },
      ...
    ]
```

### 2. 作为 Session 时间记录（在 Chronicle 内）
```python
Session
  └─ time_segments: [
      TimeSegment { started_at, ended_at, category: "work", ... },
      ...
    ]
```

**重要**：这两个是完全独立的概念！

---

## 测试覆盖率目标

| 层级 | 目标 | 优先级 |
|---|---|---|
| Domain Layer | 95%+ | 🔴 Critical |
| Service Layer | 85%+ | 🔴 Critical |
| Repository Layer | 80%+ | 🟡 High |
| Router Layer | 75%+ | 🟡 High |
| Integration | 60%+ | 🟢 Medium |

---

## Git 提交规范

**第一次提交**（基础设施）：
```
chore: v3 架构初始化 + DDD 规则系统

- 创建完整的后端和前端目录结构
- 编写 DDD_RULES.yaml（25+14 规则）
- 编写架构分析文档
```

**Domain 实现提交**：
```
feat(library): 实现 Library Domain 聚合根

- 定义 Library 实体（RULE-001 到 RULE-003）
- 实现 LibraryRepository 接口
- 编写 95% 覆盖率的单元测试

关联规则: RULE-001, RULE-002, RULE-003
关联 DevLog: D30-Library-Domain
```

**Service 实现提交**：
```
feat(library): 实现 LibraryService 业务逻辑

- 实现 create_library()
- 实现 get_library_by_user()
- 编写集成测试
```

---

## 常见问题

### Q: Block 的 metadata 结构是什么？
A: 它是一个灵活的 JSON 对象，每个 Block type 定义自己的字段。例如：
```python
# text Block
{ "language": "zh-CN", "formatting": {...} }

# code Block
{ "language": "python", "theme": "dark", "lineNumbers": true }

# checkpoint Block
{ "status": "done", "completed_at": "2025-11-10T..." }
```

### Q: Book 何时应该级联删除 vs 孤立处理？
A:
- **级联删除**：适合"彻底删除"的情况，会删除所有 Blocks 和媒体
- **孤立处理**：适合"清理分类"的情况，Books 变为自由（bookshelf_id = null）

**推荐**：默认使用孤立处理，让用户选择是否级联删除

### Q: Chronicle 与 Checkpoint Block 如何协作？
A: 它们是两个独立系统：
- **Checkpoint Block**：Book 内的标记（如"第一章完成"）
- **Chronicle Session**：记录工作时间的会话

如果用户完成了某个 Checkpoint Block，可以在 Chronicle 中创建一个 TimeSegment 来记录时间投入。

### Q: 如何处理老数据迁移？
A: 编写 Migration 脚本（在 `backend/api/migrations/versions/` 下）：
1. 将 OrbitBookshelf → Bookshelf（直接复制）
2. 将 OrbitNote → Book（直接复制）
3. 将 OrbitNote.blocks_json 扁平化 → Block 表
4. 将 OrbitTag → Tag（直接复制）
5. 更新所有外键引用

---

## 推荐学习顺序

1. ✅ 阅读 `DOMAIN_ANALYSIS.md`（理解整体）
2. ✅ 阅读 `DDD_RULES.yaml`（理解规则）
3. ✅ 阅读 `IMPLEMENTATION_GUIDE.md`（了解步骤）
4. ✅ 查看此快速参考（日常查询）
5. 🚀 开始实现 Library Domain

---

## 有用的 SQL 查询

### 迁移检查
```sql
-- 检查 Book 与 Bookshelf 的关联
SELECT COUNT(*) FROM books WHERE bookshelf_id IS NULL;

-- 检查孤立 Blocks
SELECT COUNT(*) FROM blocks WHERE book_id NOT IN (SELECT id FROM books);

-- 检查 Tag 使用频率
SELECT tag_id, COUNT(*) as count FROM book_tags GROUP BY tag_id ORDER BY count DESC;
```

### 性能优化
```sql
-- 创建索引
CREATE INDEX idx_book_bookshelf_id ON books(bookshelf_id);
CREATE INDEX idx_block_book_id ON blocks(book_id);
CREATE INDEX idx_block_order ON blocks(book_id, order);
CREATE INDEX idx_tag_name ON tags(name);
```

---

**更新于**: 2025-11-10
**版本**: v3 初始规划
