# Wordloom v3 重构详细指导文档

**作者**: 架构分析团队
**日期**: 2025-11-10
**状态**: 已分析完毕，可立即开始实现

---

## 总体情况总结

你的三天工作+本次分析已经完成了重构的**知识和规划阶段**。现在有了：

1. ✅ **完整的目录结构**（后端和前端）
2. ✅ **蓝绿部署配置**（.gitignore）
3. ✅ **老架构完整分析**（DOMAIN_ANALYSIS.md）
4. ✅ **DDD 规则系统**（DDD_RULES.yaml）

**现在可以进入实现阶段了**。

---

## 第一部分：文件关系快速回顾

### 老架构（WordloomBackend/orbit）的核心数据流

```
User
  └─ WorkSpace（隐式）
      └─ OrbitBookshelf （"书橱"表）
          ├─ name: "Python 学习"
          ├─ tags: ["技术", "编程"]
          └─ notes: [OrbitNote, OrbitNote, ...]
              └─ OrbitNote（"笔记"表）
                  ├─ title: "Python 基础"
                  ├─ content_md: "Markdown 内容"
                  ├─ blocks_json: [
                  │   { id: "b1", type: "text", content: "..." },
                  │   { id: "b2", type: "code", content: "..." },
                  │   { id: "b3", type: "image", url: "..." }
                  │ ]
                  ├─ tags: ["Python", "基础"]  ← 来自 OrbitTag 多对多关联
                  ├─ checkpoints: [  ← 嵌套在 Note 内
                  │   {
                  │     title: "第一章完成",
                  │     status: "done",
                  │     markers: [  ← 时间分片
                  │       {
                  │         started_at: "2025-11-10 09:00",
                  │         ended_at: "2025-11-10 10:30",
                  │         category: "work",
                  │         duration: 5400s
                  │       }
                  │     ]
                  │   }
                  │ ]
                  └─ media: [OrbitMediaResource, ...]

Tags（全局）
  ├─ OrbitTag: { name: "Python", color: "#3b82f6", ... }
  ├─ OrbitTag: { name: "Frontend", color: "#e11d48", ... }
  └─ ... 通过 OrbitNoteTag 关联表连接到多个 Notes
```

### v3 新架构（backend）的数据流

```
User
  └─ Library（新增，用户唯一）
      └─ Bookshelf （"书架"）
          ├─ name: "Python 学习"
          ├─ tags: ["技术", "编程"]  ← 现在是 Tag IDs，不是字符串
          └─ books: [Book, Book, ...]
              └─ Book （新名字，来自 Note）
                  ├─ title: "Python 基础"
                  ├─ summary: "摘要"
                  ├─ preview_image: "URL"
                  └─ blocks: [Block, Block, ...]  ← 扁平化
                      ├─ Block { type: "text", content: "..." }
                      ├─ Block { type: "code", content: "...", metadata: {...} }
                      ├─ Block { type: "image", content: "URL", metadata: {...} }
                      └─ Block { type: "checkpoint", metadata: {...} }  ← 变成 Block 类型

Chronicle（新增，独立模块）
  └─ Session （会话，与 Book 可选绑定）
      ├─ started_at: "2025-11-10 09:00"
      ├─ ended_at: "2025-11-10 17:30"
      ├─ book_id: (optional) "book-uuid"  ← 关联到具体的 Book
      ├─ tags: [Tag, Tag, ...]  ← 工作类型标签
      └─ time_segments: [TimeSegment, ...]  ← 工作分片
          └─ TimeSegment {
              started_at, ended_at, category, duration,
              image_urls, tags
            }

Tags（全局，与 Books 多对多）
  ├─ Tag: { id: "tag-1", name: "Python", color: "#3b82f6", ... }
  ├─ Tag: { id: "tag-2", name: "Frontend", color: "#e11d48", ... }
  └─ ... 通过 BookTag 关联表连接到多个 Books

Media（统一管理）
  ├─ MediaResource { entity_type: "bookshelf_cover", entity_id: "bs-uuid", ... }
  ├─ MediaResource { entity_type: "book_cover", entity_id: "book-uuid", ... }
  ├─ MediaResource { entity_type: "block_image", entity_id: "block-uuid", ... }
  └─ MediaResource { entity_type: "chronicle_attachment", entity_id: "session-uuid", ... }
```

---

## 第二部分：后端新架构各模块的角色

### 1. **Library 模块** （最高层，新增）

**职责**：
- 用户的数据容器和权限边界
- 每个用户只有一个 Library
- 将来支持分享、导出、备份

**核心文件**：
```
backend/api/app/modules/library/
├─ __init__.py
├─ domain.py          ← Library 聚合根定义
├─ models.py          ← ORM: Library 表
├─ schemas.py         ← API 请求/响应
├─ repository.py      ← 数据访问接口
├─ service.py         ← 业务逻辑
├─ router.py          ← FastAPI 路由
└─ tests/
   ├─ test_domain.py
   ├─ test_service.py
   └─ test_integration.py
```

**关键约束**（来自 RULE-001 到 RULE-003）：
- ✅ User 1:1 Library
- ✅ 不能删除（只能归档）
- ✅ 不能创建多个

---

### 2. **Bookshelf 模块** （第一级分类）

**职责**：
- Book 的容器和分类组织
- 可无限创建
- 支持优先级、紧急度、标签等属性

**核心文件**：
```
backend/api/app/modules/bookshelf/
├─ __init__.py
├─ domain.py          ← Bookshelf 聚合根
├─ models.py          ← ORM: Bookshelf 表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**重要操作**（来自老架构 BookshelfService）：
- ✅ 创建、读取、列表、更新、删除
- ✅ 支持转移 Books（从一个 Bookshelf 到另一个）
- ✅ 级联删除 Books 或孤立处理
- ✅ 统计 note_count（保留用于性能）

**迁移注意**：
- 老的 `bookshelf_service.py` 中的业务逻辑要复制到新 service.py
- 支持"孤立处理"的选项保留

---

### 3. **Book 模块** （内容容器）

**职责**：
- 存储结构化内容（Blocks）
- 对应老架构的 OrbitNote
- 支持复制、转移

**核心文件**：
```
backend/api/app/modules/book/
├─ __init__.py
├─ domain.py          ← Book 聚合根
├─ models.py          ← ORM: Book 表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**重要操作**（来自老架构 NoteService）：
- ✅ 创建、读取、列表、更新、删除
- ✅ **复制 Book 及其所有 Blocks**（这是 v3 中一个关键操作）
- ✅ 转移到其他 Bookshelf
- ✅ 复制上传文件夹（媒体）

**新增字段**：
- `blocks`: List[Block] （关系，代替老的 blocks_json）
- `storage_path`: 固定路径 `books/{book_id}/`

**迁移注意**：
- 老的 `blocks_json` (Text) 需要在迁移脚本中扁平化为 Block 表
- 注意 `NoteService.duplicate_note()` 的逻辑也要保留

---

### 4. **Block 模块** （最小单位）

**职责**：
- 最小的内容单位
- 支持多种 type（text, code, image, table, checkpoint, translation, media）
- 有序排列

**核心文件**：
```
backend/api/app/modules/block/
├─ __init__.py
├─ domain.py          ← Block 实体（可能变成 Value Object）
├─ models.py          ← ORM: Block 表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**重要操作**：
- ✅ 创建、读取、更新、删除
- ✅ 重新排序（移动 Block 位置）
- ✅ 变更 Block 类型

**Block 类型及其 metadata**：
```python
# text Block
{
  "type": "text",
  "content": "这是文本内容",
  "metadata": {
    "language": "zh-CN",
    "formatting": { "bold": [...], "italic": [...] }
  }
}

# code Block
{
  "type": "code",
  "content": "print('hello')",
  "metadata": {
    "language": "python",
    "theme": "dark",
    "lineNumbers": true
  }
}

# image Block
{
  "type": "image",
  "content": "storage/block_image/block-uuid/image.jpg",
  "metadata": {
    "alt": "图片描述",
    "width": 800,
    "height": 600,
    "caption": "这是一张图片"
  }
}

# checkpoint Block（从老 Checkpoint 迁移）
{
  "type": "checkpoint",
  "content": "第一章完成检查点",
  "metadata": {
    "status": "done",
    "completed_at": "2025-11-10T10:30:00Z"
  }
}

# translation Block（未来功能，可嵌套）
{
  "type": "translation",
  "content": "翻译原文",
  "metadata": {
    "source_lang": "en",
    "target_lang": "zh",
    "nested_blocks": [...]  ← 可包含其他 Blocks
  }
}
```

---

### 5. **Tag 模块** （全局标签）

**职责**：
- 全局标签系统（全局唯一）
- 与 Books 多对多关联
- 菜单栏绑定，支持过滤

**核心文件**：
```
backend/api/app/modules/tag/
├─ __init__.py
├─ domain.py
├─ models.py          ← ORM: Tag 和 BookTag 关联表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**重要操作**：
- ✅ 创建、读取、列表、更新、删除
- ✅ 关联/取消关联 Tag 到 Book
- ✅ 菜单栏过滤（按 Tag 查询 Books）

**迁移注意**：
- 老的 `OrbitTag` 表直接迁移
- 老的 `OrbitNoteTag` 关联表改名为 `BookTag`

---

### 6. **Chronicle 模块** （时间追踪，新增）

**职责**：
- 会话级别的时间追踪
- 从老架构的 Checkpoint/Marker 独立出来
- 与 Book 可选绑定，支持 Tag 标记

**核心文件**：
```
backend/api/app/modules/chronicle/
├─ __init__.py
├─ domain.py          ← Session 和 TimeSegment
├─ models.py          ← ORM: Session 和 TimeSegment 表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**核心实体**：
```python
class Session(AggregateRoot):
    id: UUID
    user_id: UUID
    book_id: UUID | None  # 可选关联到 Book
    started_at: datetime
    ended_at: datetime | None  # None = 进行中
    title: str
    tags: List[UUID]  # Tag IDs
    time_segments: List[TimeSegment]

class TimeSegment(ValueObject):
    id: UUID
    session_id: UUID
    started_at: datetime
    ended_at: datetime
    duration_seconds: int  # 自动计算
    category: str  # work, pause, break, review, etc.
    image_urls: List[str]  # 最多 5 张图片
    tags: List[UUID]  # Tag IDs
```

**迁移注意**：
- 老的 `OrbitNoteCheckpoint` 可以保留（暂不迁移）
- 未来的 Checkpoint Block 类型会与 Chronicle 集成

---

### 7. **Media 模块** （媒体管理）

**职责**：
- 统一的媒体资源存储
- 支持多种 entity_type
- 软删除策略

**核心文件**：
```
backend/api/app/modules/media/
├─ __init__.py
├─ domain.py
├─ models.py          ← ORM: MediaResource 表
├─ schemas.py
├─ repository.py
├─ service.py
├─ router.py
└─ tests/
```

**支持的 entity_type**：
- `bookshelf_cover` - Bookshelf 封面
- `book_cover` - Book 封面
- `block_image` - Block 内图片
- `chronicle_attachment` - 会话附件

**迁移注意**：
- 老的 `OrbitMediaResource` 表直接迁移
- 新增支持的 entity_type

---

### 8. **Search 模块** （搜索）

**职责**：
- 全文搜索 Books/Blocks
- 多条件组合过滤

**核心功能**：
- 按关键词搜索
- 按 Tag 过滤
- 按优先级/紧急度过滤
- 按时间范围搜索

**实现建议**：
- 使用 PostgreSQL 的 `to_tsvector` / `plainto_tsquery` 实现全文搜索
- 或集成 Elasticsearch（可选）

---

### 9. **Stats 模块** （统计）

**职责**：
- 统计数据聚合
- Dashboard 数据支持

**主要指标**：
- Books/Bookshelves/Blocks 总数
- 创建/修改趋势
- Tag 使用频率
- 工作时间统计

---

### 10. **Theme 模块** （主题）

**职责**：
- 用户界面主题管理
- 主题同步

---

## 第三部分：后端文件结构验证

### ✅ 已正确创建的文件夹

你的 PowerShell 命令正确地创建了所有必要的目录。检查：

```powershell
# 验证命令（在项目根目录运行）
Get-ChildItem -Path "backend/api/app/modules" -Directory | Select-Object Name
```

**应该看到**：
```
auth
block
book
bookshelf
chronicle
library
media
search
stats
tag
theme
```

### ⚠️ 需要补充的文件

每个 module 目录下需要创建以下文件：

```
backend/api/app/modules/library/
├─ __init__.py           ← 空文件或导出模块公共接口
├─ domain.py             ← Domain Model（AggregateRoot）
├─ models.py             ← ORM Model（SQLAlchemy）
├─ schemas.py            ← Pydantic Schema（API 请求/响应）
├─ repository.py         ← Repository 接口
├─ service.py            ← Business Logic Service
├─ router.py             ← FastAPI Router
└─ tests/
   ├─ __init__.py
   ├─ test_domain.py      ← Unit Tests for Domain
   ├─ test_service.py     ← Unit Tests for Service
   └─ test_integration.py ← Integration Tests
```

**快速创建脚本**：

```powershell
# 为每个 module 创建基础文件
$modules = @("library", "bookshelf", "book", "block", "tag", "media", "chronicle", "search", "stats", "theme")

foreach ($module in $modules) {
    $path = "backend/api/app/modules/$module"

    # 创建 __init__.py
    New-Item -Path "$path/__init__.py" -ItemType File -Force | Out-Null

    # 创建核心文件
    @("domain.py", "models.py", "schemas.py", "repository.py", "service.py", "router.py") | ForEach-Object {
        New-Item -Path "$path/$_" -ItemType File -Force | Out-Null
    }

    # 创建 tests 目录
    New-Item -Path "$path/tests/__init__.py" -ItemType File -Force | Out-Null
    New-Item -Path "$path/tests/test_domain.py" -ItemType File -Force | Out-Null
    New-Item -Path "$path/tests/test_service.py" -ItemType File -Force | Out-Null
}

Write-Host "✅ 所有 module 文件已创建"
```

---

## 第四部分：v3 中各模块的新角色和变化

### Chronicle 模块的关键变化

**老架构**：
```python
# OrbitNoteCheckpoint 存在 Note 内
OrbitNote
  └─ checkpoints: [OrbitNoteCheckpoint, ...]
      └─ markers: [OrbitNoteCheckpointMarker, ...]
```

**v3**：
```python
# 分为两部分：

# 1. Block 中的 Checkpoint（记录标记）
Book
  └─ blocks: [Block, ...]
      └─ Block { type: "checkpoint", metadata: {...} }

# 2. Chronicle Session（时间追踪）
Session
  └─ time_segments: [TimeSegment, ...]
```

**重要**：这是 v3 的核心改变之一！

---

### Tag 模块的变化

**老架构**：
```python
# Tags 存储为 ARRAY<Text> 在 Note 中
OrbitNote.tags = ["Python", "基础"]  # 字符串数组

# 同时也有关系表 OrbitNoteTag
OrbitNote N:N OrbitTag
```

**v3**：
```python
# Tags 只通过关系表，不再存储字符串
Book N:N Tag（通过 BookTag 关联表）

# Tag 支持颜色、图标等属性
Tag {
    id: UUID,
    name: str,  # 唯一
    color: str,
    icon: str,
    ...
}

# 菜单栏可以点击 Tag 来过滤 Books
```

---

### Media 模块的变化

**老架构**：
```python
# MediaEntityType 支持的类型
BOOKSHELF_COVER = "bookshelf_cover"
NOTE_COVER = "note_cover"
CHECKPOINT_MARKER = "checkpoint_marker"
IMAGE_BLOCK = "image_block"
OTHER_BLOCK = "other_block"
```

**v3**：
```python
# 增加新的类型
BOOKSHELF_COVER = "bookshelf_cover"      # 保留
BOOK_COVER = "book_cover"                # 新的（对应 NOTE_COVER）
BLOCK_IMAGE = "block_image"              # 新的
CHRONICLE_ATTACHMENT = "chronicle_attachment"  # 新的
```

---

## 第五部分：现在应该做什么？

### 🎯 接下来的步骤（优先级排序）

#### **步骤 1：创建所有 module 的基础文件**（30 分钟）

运行上面的 PowerShell 脚本，为所有 module 创建空文件。

#### **步骤 2：实现 Phase 1（基础 Domain 层）**（1-2 天）

优先顺序：
1. Library Domain （最简单）
2. Bookshelf Domain （中等复杂度）
3. Book Domain （中等复杂度）
4. Block Domain （中等复杂度）
5. Tag Domain （简单）

**每个 Domain 的实现检查清单**：
```
☐ domain.py - 定义 AggregateRoot 或 ValueObject
☐ models.py - 定义 ORM Model
☐ schemas.py - 定义请求/响应 Schema
☐ tests/test_domain.py - Unit tests
  ☐ 测试不变量（Invariants）
  ☐ 测试验证规则
  ☐ 测试工厂方法
```

**示例：Library Domain**

```python
# domain.py
from uuid import UUID
from datetime import datetime
from typing import List

class Library:
    """Library 聚合根 - 用户的唯一数据容器"""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        created_at: datetime,
        updated_at: datetime,
    ):
        # 验证不变量
        if not user_id:
            raise ValueError("user_id 不能为空")
        if not name or name.strip() == "":
            raise ValueError("name 不能为空")

        self.id = id
        self.user_id = user_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(user_id: UUID, name: str) -> "Library":
        """创建新 Library"""
        import uuid
        return Library(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
```

#### **步骤 3：实现 Phase 2（Repository + Service）**（2-3 天）

```
☐ repository.py - 数据访问接口（基于 SQLAlchemy）
☐ service.py - 业务逻辑
☐ tests/test_integration.py - 集成测试
```

#### **步骤 4：实现 Phase 3（API Router）**（1-2 天）

```
☐ router.py - FastAPI 路由
☐ tests/test_router.py - API 测试
```

#### **步骤 5：迁移脚本**（1 周）

```python
# backend/api/migrations/xxx_migrate_orbit_to_v3.py
# 将老架构数据迁移到新架构
```

---

## 第六部分：如何做到"事事有反馈，件件有回音"

### DDD Rules 与 Wordloom 日记的闭环

**目标**：每个代码变更都有对应的日记条目，每个业务规则都有代码实现。

**实现方法**：

1. **建立映射表** `.devlog/RULES_TO_ENTRIES.md`：
```markdown
| Rule ID | 规则描述 | 代码文件 | DevLog 条目 | PR | 状态 |
|---------|---------|--------|-----------|----|----|
| RULE-001 | Library 单实例 | library/domain.py:15-30 | D30-001 | #PR-001 | ✅ |
| RULE-002 | Library user 关联 | library/domain.py:32-45 | D30-002 | #PR-001 | ✅ |
| ... | ... | ... | ... | ... | ... |
```

2. **在代码中添加 Rule 标记**：
```python
# backend/api/app/modules/library/domain.py

class Library:
    """
    RULE-001: 每个用户只拥有一个 Library
    RULE-002: Library 必须关联到一个有效的 User
    RULE-003: Library 包含唯一的名称
    """

    def __init__(self, ...):
        # RULE-001: 验证 user_id 唯一性
        if not user_id:
            raise ValueError("RULE-001 violation: user_id 不能为空")
```

3. **在 Wordloom 中创建对应的日记条目**：
```
标题: D30-Library-Domain 实现完成
Tags: #DDD #Architecture #RULE-001 #RULE-002 #RULE-003
Checkpoints:
  ✓ domain.py 实现 (RULE-001, RULE-002, RULE-003)
  ✓ test_domain.py 完成 (覆盖率 95%)
  ✓ PR #001 已提交
内容:
  - Library Domain 定义完成
  - 所有不变量已验证
  - 链接: github.com/repo/pull/001
  - Code Block: (Link to domain.py)
```

4. **建立 DevLog 模板**：
```markdown
# Day 30: Library Domain 实现

## 目标
实现 Library 聚合根，完成 RULE-001 到 RULE-003

## 完成内容
- ✅ domain.py: 定义 Library 类
- ✅ test_domain.py: 95% 覆盖率
- ✅ PR #001 已提交

## 关联规则
- RULE-001: 每个用户只拥有一个 Library
- RULE-002: Library 必须关联到一个有效的 User
- RULE-003: Library 包含唯一的名称

## 代码链接
https://github.com/repo/blob/branch/backend/api/app/modules/library/domain.py

## 下一步
- 实现 Bookshelf Domain
```

---

## 第七部分：Git 第一次提交

当你完成了上面的准备工作后，运行：

```bash
cd d:\Project\Wordloom

# 检查状态
git status

# 添加所有变更
git add .

# 提交
git commit -m "chore: v3 架构初始化和 DDD 规则系统建立

- 创建 backend/api 完整目录结构
- 创建 frontend 完整目录结构
- 配置蓝绿部署 .gitignore
- 编写 DOMAIN_ANALYSIS.md（基于老架构完整分析）
- 编写 DDD_RULES.yaml（25 条不变量 + 14 条业务政策）
- 建立 5 阶段实现计划

对应 Wordloom 日记: D30-Infrastructure-Init"

# 推送
git push origin refactor/infra/blue-green-v3
```

---

## 总结：你现在的位置

```
蓝绿部署进度条：
[████████████████████████░░░░░░░░░░░░░░░░░░░░] 50%

✅ 完成：
  - 架构分析和规划
  - 文件夹结构创建
  - DDD 规则系统建立
  - 蓝绿部署配置

🚀 即将开始：
  - Library Domain 实现（下一步）
  - Bookshelf Domain 实现
  - Book Domain 实现
  - Block Domain 实现
  - ...
```

---

**下一次 Action**：

1. ✅ 创建所有 module 的基础文件（使用 PowerShell 脚本）
2. ✅ 开始实现 Library Domain（最简单，最快看到成果）
3. ✅ 为每个 Rule 编写单元测试
4. ✅ 在 Wordloom 日记中记录进度
5. ✅ 提交 PR 和 DevLog 条目

**预计时间**：
- Library Domain: 4-6 小时
- Bookshelf Domain: 6-8 小时
- Book Domain: 8-10 小时
- Block Domain: 10-12 小时
- Tag + Media: 8-10 小时
- 总计 Phase 1-2: **1.5-2 周**

祝重构顺利！🚀
