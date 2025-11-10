# Wordloom v3 Domain 分析报告

**分析日期**: 2025-11-10
**基于**: WordloomBackend 老架构 + Wordloom v3 新业务需求
**作者**: 架构重构团队

---

## 第一部分：老架构（Orbit）的文件关系图

### 老架构的核心数据模型

```
OrbitBookshelf（书橱）
  ├─ 主要职责：组织和分类 Notes
  ├─ 关键字段：
  │   ├─ id (UUID) - 唯一标识
  │   ├─ name (Text) - 书橱名称
  │   ├─ description (Text) - 描述
  │   ├─ cover_url (Text) - 封面图 URL
  │   ├─ icon (Text) - 小图标（Lucide 图标名）
  │   ├─ priority (Integer 1-5) - 优先级
  │   ├─ urgency (Integer 1-5) - 紧急度
  │   ├─ tags (ARRAY<Text>) - 标签列表（简单数组）
  │   ├─ color (Text) - 主题色
  │   ├─ status (Text) - 状态（active|archived|deleted）
  │   ├─ is_favorite (Boolean) - 收藏标记
  │   ├─ is_pinned (Boolean) - 置顶标记
  │   ├─ note_count (Integer) - 冗余计数（性能优化）
  │   └─ usage_count (Integer) - 使用次数统计
  │
  └─ 1:N 关系 → OrbitNote
        └─ 通过 bookshelf_id 外键关联

OrbitNote（笔记 = v3 中的 Book）
  ├─ 主要职责：存储实际内容（markdown + blocks）
  ├─ 关键字段：
  │   ├─ id (UUID) - 唯一标识
  │   ├─ bookshelf_id (FK to OrbitBookshelf) - 所属书橱
  │   ├─ title (Text) - 笔记标题
  │   ├─ summary (Text) - 摘要/描述
  │   ├─ content_md (Text) - Markdown 内容
  │   ├─ blocks_json (Text) - JSON 格式的 blocks 数组（**v3 中变成嵌套结构**）
  │   ├─ preview_image (Text) - 封面图 URL
  │   ├─ storage_path (Text, unique) - 固定存储路径：notes/{note_id}
  │   ├─ priority (Integer 1-5) - 优先级
  │   ├─ urgency (Integer 1-5) - 紧急度
  │   ├─ usage_level (Integer 1-5) - 日用程度
  │   ├─ usage_count (Integer) - 使用次数
  │   ├─ tags (ARRAY<Text>) - 标签列表（向后兼容的旧字段）
  │   ├─ status (Text) - 状态（open|...）
  │   ├─ is_pinned (Boolean) - 置顶标记
  │   └─ due_at (DateTime) - 截止日期
  │
  └─ N:N 关系 → OrbitTag（通过 OrbitNoteTag 关联表）

OrbitTag（标签）
  ├─ 主要职责：全局标签系统（菜单栏绑定）
  ├─ 关键字段：
  │   ├─ id (UUID)
  │   ├─ name (Text, unique) - 标签名称
  │   ├─ color (Text) - 标签颜色
  │   ├─ icon (Text) - 标签图标
  │   ├─ count (Integer) - 使用次数缓存
  │   └─ description (Text) - 描述
  │
  └─ N:N 关系 → OrbitNote（通过 OrbitNoteTag 关联表）

OrbitNoteCheckpoint（检查点 = 工作单元）
  ├─ 主要职责：Note 内的工作分解（时间追踪）
  ├─ 归属：Note 内的嵌套结构
  ├─ 关键字段：
  │   ├─ id (UUID)
  │   ├─ note_id (FK to OrbitNote)
  │   ├─ title (String) - 检查点标题
  │   ├─ status (String) - pending|in_progress|on_hold|done
  │   ├─ started_at (DateTime) - 开始时间
  │   ├─ completed_at (DateTime) - 完成时间
  │   └─ markers (1:N relationship) → OrbitNoteCheckpointMarker
  │
  └─ 计算属性：
      ├─ duration_seconds - 总工作时长
      └─ completion_percentage - 完成度百分比

OrbitNoteCheckpointMarker（时间标记）
  ├─ 主要职责：工作分段记录（时间片段）
  ├─ 归属：Checkpoint 内的嵌套结构
  ├─ 关键字段：
  │   ├─ id (UUID)
  │   ├─ checkpoint_id (FK to OrbitNoteCheckpoint)
  │   ├─ title (String) - 标记标题
  │   ├─ started_at (DateTime) - 开始时间
  │   ├─ ended_at (DateTime) - 结束时间
  │   ├─ duration_seconds (Integer) - 时长
  │   ├─ category (String) - work|pause|bug|feature|review|custom
  │   ├─ image_urls (JSONB) - 最多 5 张图片（60x60）
  │   ├─ is_completed (Boolean) - 完成标记
  │   ├─ color (String) - UI 颜色
  │   ├─ emoji (String) - UI 表情
  │   └─ tags (JSONB) - Tag ID 列表

OrbitMediaResource（媒体资源）
  ├─ 主要职责：统一的媒体存储管理
  ├─ 关键字段：
  │   ├─ id (UUID)
  │   ├─ workspace_id (UUID) - 所属工作区
  │   ├─ entity_type (Enum) - BOOKSHELF_COVER|NOTE_COVER|CHECKPOINT_MARKER|IMAGE_BLOCK|OTHER_BLOCK
  │   ├─ entity_id (UUID) - 关联的实体 ID
  │   ├─ file_name (String) - 文件名
  │   ├─ file_path (String) - 物理路径
  │   ├─ file_size (Integer) - 文件大小
  │   ├─ mime_type (String) - MIME 类型
  │   ├─ file_hash (String) - SHA256 哈希
  │   ├─ width, height (Integer) - 图片尺寸
  │   └─ is_thumbnail (Boolean) - 是否缩略图

```

### 数据流关系

```
User
  └─ Workspace（隐式，通常与 User 1:1）
      └─ OrbitBookshelf（可多个）
          ├─ name = "Python Learning"
          └─ notes 数组（1:N）
              ├─ OrbitNote（id: "note-001"）
              │   ├─ title = "Python 基础"
              │   ├─ blocks_json = [
              │   │   { type: "text", content: "..." },
              │   │   { type: "code", content: "..." },
              │   │   { type: "image", url: "..." }
              │   │ ]
              │   ├─ tags_rel → [OrbitTag, OrbitTag, ...]（通过 OrbitNoteTag 关联）
              │   └─ checkpoints（嵌套数组，未来在 v3 变成 Chronicle）
              │       └─ OrbitNoteCheckpoint
              │           ├─ title = "完成第一章"
              │           └─ markers（时间分片）
              │
              └─ OrbitNote（id: "note-002"）
                  └─ ...

Tags（全局）
  ├─ OrbitTag（id: "tag-1"）- name: "Python"
  ├─ OrbitTag（id: "tag-2"）- name: "Frontend"
  └─ ... 通过 OrbitNoteTag 与多个 Note 关联
```

---

## 第二部分：老架构 → v3 的映射关系

### 数据模型映射

| 老架构（Orbit） | 新架构（v3） | 备注 |
|---|---|---|
| **OrbitBookshelf** | **Bookshelf** | 直接映射，但在 v3 中成为 Library 下的一级容器 |
| **OrbitNote** | **Book** | 直接映射，存储实际内容 |
| (no direct entity) | **Block** | 从 OrbitNote.blocks_json 扁平化出来的独立实体 |
| **OrbitTag** | **Tag** | 直接映射，保持全局标签系统 |
| **OrbitNoteCheckpoint** | ❌ 迁移到 **Chronicle** | checkpoint 的"计时功能"被移动到新的 Chronicle 模块 |
| **OrbitMediaResource** | **MediaResource** | 直接映射，统一媒体管理 |

### 重要的业务逻辑迁移

#### 1. **Blocks 的结构化** ✅

**老架构**：
```python
# OrbitNote.blocks_json 是一个 JSON 字符串
blocks_json = "[
  { \"type\": \"text\", \"content\": \"...\", \"id\": \"block-1\" },
  { \"type\": \"code\", \"content\": \"...\", \"id\": \"block-2\" }
]"
```

**v3**：
```python
# 变成独立的 Block 实体
class Block(AggregateRoot):
    id: UUID
    book_id: UUID  # 属于 Book
    type: str  # "text", "code", "image", "table", "checkpoint", etc.
    content: str
    metadata: Dict  # 类型特定的元数据
    order: int  # 排序
```

#### 2. **Checkpoint 的新角色** 📍

**老架构**：Checkpoint 存储在 OrbitNote 内，用于记录时间分片和工作状态

**v3**：
- **CheckPoint Block**：Note/Book 内的一个特殊 Block 类型，用于标记检查点
- **Chronicle Module**：新独立模块，用于存储会话级别的时间追踪和日志

**示例**：
```
Book: "Python Learning"
  ├─ Block 1 (type: text) - "基础概念"
  ├─ Block 2 (type: checkpoint) - "第一章完成检查点"  ← 从 Checkpoint 迁移来
  ├─ Block 3 (type: code)
  └─ Block 4 (type: translation) - 未来的翻译 Block，可能包含嵌套结构

Chronicle: "2025-11-10 工作日记"
  └─ Session 1
      ├─ 工作时段 1 (09:00-10:30) - 完成 Book "Python Learning"
      ├─ 工作时段 2 (11:00-12:00) - 总结
      └─ 统计信息（总耗时、完成率）
```

#### 3. **Tag 的新角色** 🏷️

**老架构**：OrbitTag 与 OrbitNote 通过多对多关系绑定，用于分类

**v3**：
- **Tag 仍然是全局的**，与 Book 多对多关系
- **关联到菜单栏**：用户可以点击 Tag 来过滤/搜索
- **可选**：在 Block 级别也可以有 tags（用于细粒度标记）

#### 4. **Media 的新角色** 📸

**老架构**：OrbitMediaResource 存储各种媒体资源

**v3**：
- **保持统一的媒体管理**
- **新增实体类型**：
  - `bookshelf_cover` - Bookshelf 的封面
  - `book_cover` - Book 的封面
  - `block_image` - Block 内的图片
  - `checkpoint_marker_image` - 检查点标记的图片

---

## 第三部分：v3 新架构的职责划分

### 核心模块职责

```
Library（新增）
├─ 职责：用户的数据容器和权限边界
├─ 字段：id, user_id, name, description, tags, permissions
├─ 特点：每个用户 1 个，不能删除
└─ 关系：1:N → Bookshelf

Bookshelf（来自 OrbitBookshelf）
├─ 职责：Book 的第一级分类容器
├─ 字段：id, library_id, name, description, cover_url, tags, priority, urgency
├─ 特点：可无限创建、支持嵌套标签
└─ 关系：1:N → Book

Book（来自 OrbitNote）
├─ 职责：存储结构化内容（Blocks 的容器）
├─ 字段：id, bookshelf_id, title, summary, preview_image, status
├─ 特点：包含有序的 Blocks
└─ 关系：1:N → Block

Block（新增，从 blocks_json 扁平化）
├─ 职责：最小的内容单位
├─ 字段：id, book_id, type, content, metadata, order
├─ 类型：text, code, image, table, checkpoint, translation, media, etc.
└─ 特点：可嵌套（特别是 checkpoint 和 translation 类型）

Tag（来自 OrbitTag，重新设计）
├─ 职责：全局分类标签（菜单栏绑定）
├─ 字段：id, name, color, icon, description
├─ 特点：多对多关联到 Book
└─ 用法：菜单栏点击 Tag 来过滤 Books

Chronicle（新增，从 Checkpoint 分离）
├─ 职责：会话级别的时间追踪和日志
├─ 主要实体：
│   ├─ Session（工作会话）
│   │   ├─ id, user_id, started_at, ended_at
│   │   └─ TimeSegment（时间分片）
│   │       ├─ started_at, ended_at, category, tags
│   │       └─ attachments（图片等）
│   └─ 计算数据：总耗时、完成率、效率指标
└─ 用法：在 Wordloom 日记中记录当日工作

Media（来自 OrbitMediaResource，补充新类型）
├─ 职责：统一的媒体资源管理
├─ 支持类型：图片、视频、文件等
├─ 特点：支持上传、缩略图生成、清理
└─ 集成点：Bookshelf/Book/Block/Chronicle 的媒体存储

Search（新增）
├─ 职责：全文搜索、标签过滤
├─ 支持：Books、Blocks 的内容搜索
└─ 集成：标签、优先级、紧急度等条件过滤

Stats（新增）
├─ 职责：统计数据聚合
├─ 指标：阅读次数、创建时间、标签分布等
└─ 用于：Dashboard 展示、数据分析

Preferences（新增）
├─ 职责：用户偏好和设置
├─ 包含：主题、语言、通知设置等
└─ 存储：User Profile 相关数据
```

### Module 间的数据流

```
User
  ├─ 创建 Bookshelf（Bookshelf Module）
  │   └─ 触发 BookshelfCreated 事件
  │
  ├─ 创建 Book（Book Module）
  │   ├─ 属于某个 Bookshelf
  │   ├─ 初始化为空 Blocks 列表
  │   └─ 触发 BookCreated 事件
  │
  ├─ 编辑 Block（Block Module）
  │   ├─ 添加、修改、删除 Block
  │   ├─ 处理媒体上传（Media Module）
  │   ├─ 处理标签（Tag Module）
  │   └─ 触发 BlockUpdated 事件
  │
  ├─ 记录时间（Chronicle Module）
  │   ├─ 开始/结束工作会话
  │   ├─ 添加时间分片和标记
  │   └─ 关联到具体的 Book 或 Tag
  │
  ├─ 搜索和过滤（Search Module）
  │   ├─ 按 Tag 过滤
  │   ├─ 按关键词搜索
  │   └─ 组合查询
  │
  └─ 查看统计（Stats Module）
      ├─ Books 的创建/读取趋势
      ├─ Tag 的使用频率
      ├─ 时间投入分析
      └─ 效率指标
```

---

## 第四部分：DDD 规则提取

### 核心约束（Invariants）

**核心规则来自老架构的验证**：

1. **Library 约束**：
   - ✅ 用户只能有 1 个 Library
   - ✅ Library 不能删除（只能归档）
   - ✅ Library 拥有分享/权限配置

2. **Bookshelf 约束**：
   - ✅ 必须属于 Library（FK: library_id）
   - ✅ name 不能为空
   - ✅ 可以无限创建
   - ✅ 可以在 Bookshelf 间移动 Books
   - ✅ 删除 Bookshelf 时可以选择：级联删除所有 Books 或孤立处理

3. **Book 约束**：
   - ✅ 必须属于 Bookshelf（FK: bookshelf_id）
   - ✅ title 可空（从 OrbitNote 中学到）
   - ✅ 可以无限创建
   - ✅ 包含有序的 Blocks（blocks_json → Block 数组）
   - ✅ 支持复制（复制 Book 及其所有 Blocks）
   - ✅ 可以转移到其他 Bookshelf

4. **Block 约束**：
   - ✅ 必须属于 Book（FK: book_id）
   - ✅ 必须有 type（text|code|image|checkpoint|translation|...）
   - ✅ 可以无限创建
   - ✅ 有序排列（order 字段）
   - ✅ 支持元数据（type 特定的字段存在 metadata JSON）

5. **Tag 约束**：
   - ✅ 全局唯一的标签名
   - ✅ 与 Book 多对多关系
   - ✅ 支持颜色和图标
   - ✅ 菜单栏绑定（可过滤）

6. **Media 约束**：
   - ✅ 必须关联到具体的 entity_type（BOOKSHELF_COVER|BOOK_COVER|BLOCK_IMAGE|...）
   - ✅ entity_id 必须存在
   - ✅ 文件存储路径固定：`uploads/{entity_type}/{entity_id}/`
   - ✅ 支持软删除

### 业务政策（Policies）

1. **级联删除**：
   - Library 删除时 → 所有 Bookshelves、Books、Blocks 级联删除
   - Bookshelf 删除时 → 所有 Books、Blocks 级联删除或孤立处理
   - Book 删除时 → 所有 Blocks 级联删除

2. **标签绑定**：
   - Tag 删除时 → 自动从所有 Books 移除
   - Book 删除时 → 自动清理 Tags 关联

3. **媒体清理**：
   - Block 删除时 → 自动清理关联的媒体文件
   - Media 删除时 → 同步清理物理文件

4. **时间追踪**（Chronicle）：
   - Session 与 Book 可选绑定
   - Marker 支持多个 Tag 标记
   - 自动计算 duration_seconds

---

## 第五部分：文件创建清单

### v3 Backend 文件结构检查

✅ **已正确创建的目录**：
```
backend/
├─ api/
│  ├─ app/
│  │  ├─ __init__.py ✓
│  │  ├─ config.py ✓
│  │  ├─ main.py ✓
│  │  ├─ infra/
│  │  │  ├─ __init__.py ✓
│  │  │  ├─ cache.py ✓
│  │  │  ├─ database.py ✓
│  │  │  ├─ event_bus.py ✓
│  │  │  ├─ logger.py ✓
│  │  │  └─ storage.py ✓
│  │  ├─ modules/
│  │  │  ├─ __init__.py ✓
│  │  │  ├─ library/ ✓
│  │  │  ├─ bookshelf/ ✓
│  │  │  ├─ book/ ✓
│  │  │  ├─ block/ ✓
│  │  │  ├─ tag/ ✓
│  │  │  ├─ media/ ✓
│  │  │  ├─ chronicle/ ✓
│  │  │  ├─ search/ ✓
│  │  │  ├─ stats/ ✓
│  │  │  └─ theme/ ✓
│  │  ├─ shared/
│  │  │  ├─ __init__.py ✓
│  │  │  ├─ deps.py ✓
│  │  │  ├─ errors.py ✓
│  │  │  ├─ events.py ✓
│  │  │  └─ schemas.py ✓
│  │  └─ tests/
│  │     └─ __init__.py ✓
│  ├─ migrations/
│  │  ├─ env.py ✓
│  │  ├─ script.py.mako ✓
│  │  └─ versions/ ✓
│  └─ storage/ ✓
├─ docs/
│  └─ ARCHITECTURE.md ✓
├─ Makefile ✓
└─ pyproject.toml ✓
```

⚠️ **需要补充的文件**：
```
backend/api/app/modules/*/
├─ __init__.py           ← 每个模块都需要
├─ domain.py             ← DDD 域模型
├─ repository.py         ← 数据访问接口
├─ service.py            ← 业务逻辑
├─ schemas.py            ← API 请求/响应契约
├─ router.py             ← FastAPI 路由
├─ models.py             ← ORM 数据库模型
└─ tests/
   ├─ __init__.py
   ├─ test_domain.py
   ├─ test_service.py
   └─ test_integration.py

backend/api/app/tests/
├─ conftest.py           ← pytest 全局配置
├─ test_library/
├─ test_bookshelf/
├─ test_book/
└─ ...
```

---

## 总结

### 关键发现

1. **老架构是扁平结构**：Bookshelf → Notes → blocks_json
   - 新架构：Library → Bookshelf → Book → Block（四层树形结构）

2. **Checkpoint 迁移**：从 Note 内的嵌套结构 → 独立的 Chronicle 模块
   - 时间追踪的关注点转移到会话级别而非单个 Note

3. **Tags 被重新定位**：全局标签系统 → 菜单栏绑定
   - 支持在 Tag 维度进行统计和过滤

4. **Media 统一管理**：保留 OrbitMediaResource 的设计，扩展实体类型支持

5. **业务逻辑的核心不变**：
   - 级联删除、复制、转移等操作逻辑保持一致
   - 新架构中更加清晰的职责划分

### 下一步建议

1. ✅ 完成 `DDD_RULES.yaml` 的编写（基于本分析）
2. ✅ 为每个 Module 创建 `domain.py`（定义 Aggregate Root 和 Value Objects）
3. ✅ 为每个 Module 创建 `repository.py` 接口
4. ✅ 编写 Unit Tests for Domain Layer
5. ✅ 创建 Migration Scripts 从老架构到新架构
6. ✅ 建立 API 契约文档

---

**作者备注**：本分析基于完整的代码审计，确保 v3 架构既继承了老系统的成熟经验，又提供了更清晰的分层和更好的可维护性。