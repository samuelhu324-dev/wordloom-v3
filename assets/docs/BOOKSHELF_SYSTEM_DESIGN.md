# Bookshelf 系统 - 架构设计方案

**日期**: 2025-10-31
**阶段**: 概念设计和方案论证
**目标**: 为 Orbit Notes 设计成熟的分类管理系统

---

## 📋 需求总结

### 核心功能
1. **Bookshelf 实体** — 有 ID、名称、封面图
2. **容器关系** — 一个 Bookshelf 包含多个 Notes
3. **视图模式** — 条目视图（列表）和卡片视图（Grid）
4. **搜索过滤** — 按优先级、紧急度、使用次数、关键词
5. **内容转移** — Notes 可在 Bookshelf 间移动
6. **复制行为** — Notes 复制时，副本自动落在原 Bookshelf
7. **禁用复制** — Bookshelf 本身不可复制

### 场景举例
```
Bookshelf: QuickLog
  ├─ Note: Day20-Orbit-Feature-1
  ├─ Note: Day20-Orbit-Feature-2
  └─ Note: Day20-Orbit-Feature-3

Bookshelf: ProjectX-Design
  ├─ Note: UI Wireframe
  ├─ Note: Color Palette
  └─ Note: Typography

Bookshelf: Learning
  ├─ Note: Python Tips
  └─ Note: Database Design
```

---

## 🎯 我的成熟建议

### 【第一层】数据库设计

#### 新建表：`orbit_bookshelves`

```sql
CREATE TABLE orbit_bookshelves (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,                    -- 书橱名称
  description TEXT,                      -- 描述
  cover_url TEXT,                        -- 封面图 URL
  icon TEXT,                             -- 可选：小图标
  priority INTEGER DEFAULT 3,            -- 优先级 (1-5)
  urgency INTEGER DEFAULT 3,             -- 紧急度 (1-5)
  usage_count INTEGER DEFAULT 0,         -- 使用次数
  note_count INTEGER DEFAULT 0,          -- 快速计数（冗余但查询快）
  status TEXT DEFAULT 'active',          -- 状态：active, archived, deleted
  tags TEXT[] DEFAULT '{}',              -- 分类标签
  color TEXT,                            -- 主题色（可选）
  is_favorite BOOLEAN DEFAULT FALSE,     -- 收藏标记
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by UUID,                       -- 创建者 ID（未来多用户预留）

  CONSTRAINT name_not_empty CHECK (name != '')
);

CREATE INDEX idx_bookshelves_status ON orbit_bookshelves(status);
CREATE INDEX idx_bookshelves_created_at ON orbit_bookshelves(created_at);
```

#### 修改表：`orbit_notes`

```sql
ALTER TABLE orbit_notes
ADD COLUMN bookshelf_id UUID REFERENCES orbit_bookshelves(id) ON DELETE SET NULL;

CREATE INDEX idx_notes_bookshelf ON orbit_notes(bookshelf_id);
```

---

### 【第二层】架构设计

#### 关系模型
```
Bookshelf (1) ─────→ (*) Notes
  ├─ 一个 Bookshelf 包含多个 Notes
  ├─ 一个 Note 属于最多一个 Bookshelf
  └─ Bookshelf 删除时，Notes 的 bookshelf_id 设为 NULL（变为自由 Note）
```

#### 核心概念
```
三层结构：

┌─────────────────────────────────────┐
│ 自由 Notes                           │  (bookshelf_id = NULL)
│ • 未分类的便签                      │
│ • 快速捕获的片段                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Bookshelf 系统                       │  (organized)
│ ├─ QuickLog Bookshelf               │
│ │  ├─ Note 1                        │
│ │  ├─ Note 2                        │
│ │  └─ Note 3                        │
│ └─ ProjectX Bookshelf               │
│    ├─ Note A                        │
│    └─ Note B                        │
└─────────────────────────────────────┘
```

---

### 【第三层】交互设计

#### 视图层级
```
Orbit 首页
├─ 全局视图
│  ├─ "所有 Notes"（bookshelf_id = NULL 的）
│  ├─ "Bookshelves"（列表/卡片）
│  └─ 搜索/过滤
│
└─ Bookshelf 详情页
   ├─ 封面 + 元信息（优先级、紧急度、Note 数量）
   ├─ Notes 列表/卡片视图
   ├─ 操作菜单
   │  ├─ 编辑 Bookshelf 信息
   │  ├─ 添加 Note
   │  ├─ 转移 Note（到其他 Bookshelf）
   │  ├─ 排序/过滤
   │  └─ 删除 Bookshelf
   └─ Notes 展示区
```

#### 操作流程

**创建 Bookshelf**
```
用户点击 "新建书橱"
  ↓
弹窗：名称、描述、封面图
  ↓
创建成功 → 跳转到该书橱的详情页
```

**将 Note 加入 Bookshelf**
```
方式 1：从 Note 卡片
  右键菜单 → "加入书橱" → 选择目标 Bookshelf

方式 2：拖拽（可选，高级）
  从 Note 列表拖到 Bookshelf

方式 3：从 Bookshelf 内添加
  在 Bookshelf 详情页 → "添加 Note" → 选择/搜索现有 Note
```

**转移 Note**
```
用户在 Bookshelf A 内，想移到 B
  ↓
Note 卡片 → 右键 → "移到..." → 选择 Bookshelf B
  ↓
Bookshelf A.note_count -= 1
Bookshelf B.note_count += 1
Note.bookshelf_id = B.id
```

**复制 Note**
```
原逻辑（已实现）：复制时生成新 ID
改进：复制后的新 Note 自动归到原 Bookshelf

比如：
  QuickLog 中的 Note X
    ↓ 复制
  QuickLog 中的 Note X (副本)

（副本自动留在同一个 Bookshelf）
```

---

### 【第四层】前端页面结构

#### 新增页面

**1. `/orbit/bookshelves` — Bookshelf 管理首页**
```tsx
- 顶部：搜索框 + 过滤器（优先级、紧急度等）
- 新建按钮："+ 新建书橱"
- 主区域：
  ├─ 卡片视图：每个 Bookshelf 显示封面 + 名称 + Note 数量 + 元数据
  ├─ 列表视图：表格形式
  └─ 每个书橱项：
     ├─ 封面（大图 或 小缩略图）
     ├─ 名称 + 描述
     ├─ 优先级/紧急度/使用次数
     ├─ Note 数量
     └─ 操作菜单（编辑、删除、查看）
```

**2. `/orbit/bookshelves/[id]` — Bookshelf 详情页**
```tsx
- 顶部：面包屑导航 + 返回按钮
- 封面区：大封面图 + 书橱名称 + 描述
- 元信息条：优先级、紧急度、使用次数、Note 数量、创建日期
- 操作栏：编辑 | 设置 | 更多菜单
- 搜索/过滤：针对该书橱内的 Notes
- Notes 展示：
  ├─ 卡片视图
  ├─ 列表视图
  └─ 排序选项（创建时间、更新时间、优先级等）
- 快速操作：
  ├─ "+ 添加现有 Note"
  ├─ "+ 新建 Note"
  └─ "转移 Note 到其他书橱"
```

**3. 修改 `/orbit` 首页**
```tsx
新增区域：

顶部导航：
  ├─ 所有 Notes（默认）
  ├─ 我的书橱
  ├─ 统计
  └─ 主题

"我的书橱" 区域：
  ├─ 快速访问：最近打开的 N 个书橱（卡片）
  ├─ 全部书橱：列表/卡片视图
  └─ 搜索书橱

"自由 Notes" 区域：
  ├─ 未分类的 Notes（bookshelf_id = NULL）
  └─ 建议用户整理到某个书橱
```

---

### 【第五层】核心业务逻辑

#### Bookshelf 的生命周期

**创建**
```python
def create_bookshelf(
    name: str,
    description: Optional[str] = None,
    cover_url: Optional[str] = None,
    priority: int = 3,
    urgency: int = 3,
    db: Session = None,
) -> OrbitBookshelf:
    """创建新书橱"""
    bs = OrbitBookshelf(
        name=name,
        description=description,
        cover_url=cover_url,
        priority=priority,
        urgency=urgency,
        note_count=0,
        status='active',
    )
    db.add(bs)
    db.commit()
    db.refresh(bs)
    return bs
```

**添加 Note**
```python
def add_note_to_bookshelf(
    bookshelf_id: str,
    note_id: str,
    db: Session = None,
) -> OrbitNote:
    """将 Note 添加到书橱"""
    note = db.get(OrbitNote, note_id)
    bookshelf = db.get(OrbitBookshelf, bookshelf_id)

    if not note or not bookshelf:
        raise ValueError("Note or Bookshelf not found")

    # 如果 Note 已在其他书橱，先移除（可选：检查是否允许转移）
    if note.bookshelf_id and note.bookshelf_id != bookshelf_id:
        old_bs = db.get(OrbitBookshelf, note.bookshelf_id)
        if old_bs:
            old_bs.note_count -= 1

    note.bookshelf_id = bookshelf_id
    bookshelf.note_count += 1
    db.add(note)
    db.add(bookshelf)
    db.commit()
    db.refresh(note)
    return note
```

**复制 Note 时保留 Bookshelf**
```python
def duplicate_note_in_bookshelf(
    note_id: str,
    db: Session = None,
) -> OrbitNote:
    """复制 Note，新副本落在原 Bookshelf"""
    from app.services.note_service import NoteService

    original = db.get(OrbitNote, note_id)
    service = NoteService()
    new_note = service.duplicate_note(note_id, db)

    # 关键：将新 Note 也加入原 Bookshelf
    if original.bookshelf_id:
        new_note.bookshelf_id = original.bookshelf_id
        bs = db.get(OrbitBookshelf, original.bookshelf_id)
        bs.note_count += 1
        db.add(bs)

    db.commit()
    db.refresh(new_note)
    return new_note
```

**转移 Note**
```python
def move_note_to_bookshelf(
    note_id: str,
    target_bookshelf_id: str,
    db: Session = None,
) -> OrbitNote:
    """将 Note 移到另一个 Bookshelf"""
    note = db.get(OrbitNote, note_id)
    target_bs = db.get(OrbitBookshelf, target_bookshelf_id)

    if not note or not target_bs:
        raise ValueError("Note or Bookshelf not found")

    # 从原书橱移除
    if note.bookshelf_id:
        old_bs = db.get(OrbitBookshelf, note.bookshelf_id)
        if old_bs:
            old_bs.note_count -= 1
            db.add(old_bs)

    # 加入新书橱
    note.bookshelf_id = target_bookshelf_id
    target_bs.note_count += 1

    db.add(note)
    db.add(target_bs)
    db.commit()
    db.refresh(note)
    return note
```

**删除 Bookshelf**
```python
def delete_bookshelf(
    bookshelf_id: str,
    cascade: str = "orphan",  # "orphan" 或 "delete"
    db: Session = None,
) -> bool:
    """
    删除书橱

    cascade 选项：
    - "orphan": Notes 的 bookshelf_id 设为 NULL（推荐）
    - "delete": 级联删除所有 Notes（危险！）
    """
    bs = db.get(OrbitBookshelf, bookshelf_id)
    if not bs:
        return False

    if cascade == "delete":
        # 删除所有 Notes
        db.query(OrbitNote).filter_by(bookshelf_id=bookshelf_id).delete()
    else:
        # 只是移除关联
        db.query(OrbitNote).filter_by(bookshelf_id=bookshelf_id).update(
            {OrbitNote.bookshelf_id: None}
        )

    db.delete(bs)
    db.commit()
    return True
```

---

### 【第六层】API 设计

#### 新增端点

```
POST   /api/orbit/bookshelves
GET    /api/orbit/bookshelves
GET    /api/orbit/bookshelves/{id}
PUT    /api/orbit/bookshelves/{id}
DELETE /api/orbit/bookshelves/{id}

POST   /api/orbit/bookshelves/{id}/notes          # 将 Note 加入
DELETE /api/orbit/bookshelves/{id}/notes/{note_id} # 从书橱移除
POST   /api/orbit/notes/{id}/move-to-bookshelf   # 移动 Note

GET    /api/orbit/bookshelves/{id}/notes         # 列出书橱内 Notes
```

#### Schema 设计

```python
class BookshelfOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    priority: int
    urgency: int
    usage_count: int
    note_count: int
    status: str
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class BookshelfIn(BaseModel):
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    priority: Optional[int] = 3
    urgency: Optional[int] = 3
    tags: Optional[List[str]] = None

class MoveNoteRequest(BaseModel):
    target_bookshelf_id: str
```

---

### 【第七层】前端 Hook 和服务

#### API 层 (`api.ts`)

```typescript
// 新增函数
export async function createBookshelf(payload: Partial<Bookshelf>): Promise<Bookshelf> { ... }
export async function getBookshelf(id: string): Promise<Bookshelf> { ... }
export async function listBookshelves(params?: BookshelfListParams): Promise<Bookshelf[]> { ... }
export async function updateBookshelf(id: string, payload: Partial<Bookshelf>): Promise<Bookshelf> { ... }
export async function deleteBookshelf(id: string): Promise<void> { ... }
export async function addNoteToBookshelf(bookshelfId: string, noteId: string): Promise<Note> { ... }
export async function moveNoteToBookshelf(noteId: string, targetBookshelfId: string): Promise<Note> { ... }
export async function getBookshelfNotes(bookshelfId: string): Promise<Note[]> { ... }
```

#### React Hook

```typescript
export function useBookshelf(id: string) {
  return useQuery({
    queryKey: ["bookshelf", id],
    queryFn: () => getBookshelf(id),
  });
}

export function useBookshelves() {
  return useQuery({
    queryKey: ["bookshelves"],
    queryFn: () => listBookshelves(),
  });
}

export function useMutateBookshelf() {
  const qc = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (payload: Partial<Bookshelf>) => createBookshelf(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookshelves"] }),
  });

  const moveMutation = useMutation({
    mutationFn: ({ noteId, bookshelfId }: { noteId: string; bookshelfId: string }) =>
      moveNoteToBookshelf(noteId, bookshelfId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bookshelves"] });
      qc.invalidateQueries({ queryKey: ["notes"] });
    },
  });

  return { createMutation, moveMutation };
}
```

---

### 【第八层】迁移策略

#### 从当前架构到 Bookshelf

**阶段 1：数据库（无业务中断）**
- 新建 `orbit_bookshelves` 表
- 添加 `orbit_notes.bookshelf_id` 列（允许 NULL）
- 所有现有 Notes 保持 `bookshelf_id = NULL`（自由 Notes）

**阶段 2：后端 API**
- 实现 Bookshelf 的 CRUD
- 实现 Note 转移逻辑
- 更新"复制"逻辑

**阶段 3：前端 UI**
- 新增 `/orbit/bookshelves` 页面
- 在现有 `/orbit` 页面添加 Bookshelf 区域
- 在 Note 卡片上添加"加入书橱"操作

**阶段 4：用户迁移**
- 现有 Notes 可继续使用（无强制迁移）
- 建议用户创建常用的 Bookshelves（QuickLog、ProjectX 等）
- 逐步整理 Notes 到相应书橱

---

## ⚡ 核心设计原则

### 1. **松耦合**
- Note 可独立存在（不强制 Bookshelf）
- Bookshelf 删除时 Notes 不丢失（设为 NULL）

### 2. **冗余优化**
- `note_count` 冗余但查询快
- 提供后台任务定期校验一致性

### 3. **渐进迁移**
- 不打破现有功能
- 用户可选择使用 Bookshelf 或保持自由

### 4. **统一 UX**
- Bookshelf 的交互与 Note 一致
- 都支持卡片/列表视图
- 都支持搜索/过滤

### 5. **扩展性**
- 预留 `tags` 字段（未来可按标签跨 Bookshelf 搜索）
- 预留 `color` 字段（主题化）
- 预留 `created_by`（未来多用户）

---

## 🎯 实现优先级

### 优先级 1（MVP）
- [x] 数据库设计
- [ ] 后端 CRUD API
- [ ] 前端 Bookshelf 列表页
- [ ] 前端 Bookshelf 详情页
- [ ] Note 添加到 Bookshelf 操作

### 优先级 2（完整）
- [ ] Bookshelf 内 Notes 搜索/过滤
- [ ] Note 转移到其他 Bookshelf
- [ ] 复制 Note 自动落在原 Bookshelf
- [ ] Bookshelf 编辑（名称、描述、封面）

### 优先级 3（高级）
- [ ] 拖拽 Note 到 Bookshelf
- [ ] Bookshelf 合并
- [ ] 批量转移 Notes
- [ ] 废纸篓 Bookshelf（已删除 Notes 临时存放）

### 优先级 4（产品级）
- [ ] Bookshelf 分享（未来多用户）
- [ ] Bookshelf 模板
- [ ] 自动分类 AI（根据内容推荐 Bookshelf）

---

## 💡 你可能会问的问题

### Q1：一个 Note 能属于多个 Bookshelf 吗？
**A**: 初期不支持。一个 Note 最多一个 Bookshelf（或都不属于）。
- 理由：简化逻辑，避免复杂的转移规则
- 如需多分类，后期可用"标签"实现

### Q2：能否按 Bookshelf 聚合搜索？
**A**: 可以。第 2 阶段会加 `tag:bookshelf_name` 搜索语法。

### Q3：Bookshelf 能否排序？
**A**: 支持。字段有：`created_at`、`updated_at`、`priority`、`usage_count`、`note_count`

### Q4：删除 Bookshelf 时，Notes 怎么办？
**A**: 用户选择：
- 选项 1：Notes 变为自由（`bookshelf_id = NULL`）推荐
- 选项 2：连同删除（确认后）

### Q5：能否拖拽 Notes 到 Bookshelf？
**A**: 第 3 阶段可加。基础版本用右键菜单。

---

## 📝 建议阅读顺序

1. 需求总结（理解你的需求）
2. 核心概念（理解设计思想）
3. 数据库设计（理解数据结构）
4. 交互设计（理解用户流程）
5. 业务逻辑（理解实现细节）
6. 实现优先级（理解开发计划）

---

## 🔗 后续步骤

你确认了这个方案后，我可以：

1. **详细的数据库迁移脚本** — SQL 语句 + 测试
2. **完整的后端 Service** — file_service.py + bookshelf_service.py
3. **后端路由** — 所有 API 端点的实现
4. **前端 Hook 和 API** — TypeScript 完整实现
5. **前端 UI 组件** — 页面组件

**问题**：你对这个方案满意吗？需要我调整哪些地方？
