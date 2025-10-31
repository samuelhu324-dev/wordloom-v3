# Bookshelf 系统 - 深度考量与对标分析

**日期**: 2025-10-31
**目的**: 基于已有的 Note 系统，思考 Bookshelf 设计的深层考量

---

## 🔍 设计思考

### 与现有 Note 系统的对标

| 维度 | Note | Bookshelf | 关系 |
|------|------|-----------|------|
| **主体** | 内容单元 | 容器/分类 | 1 Bookshelf : N Notes |
| **创建** | 快速 | 相对少（规划性） | Notes 可秒建，Bookshelf 是计划 |
| **复制** | 支持 | 不支持 | Notes 复制时新副本落在原 Bookshelf |
| **删除** | 清理文件夹 | 可级联清理 | Bookshelf 删除时有转移或删除选择 |
| **搜索** | 关键词、标签 | 名称、内容聚合 | 可按 Bookshelf 过滤 Notes |
| **图片** | 每 Note 一个文件夹 | Bookshelf 一个封面 | 简化，封面 URL 存数据库或专用字段 |
| **视图** | 卡片/列表 | 卡片/列表 | 一致的 UX |
| **权限** | 可预留用户标记 | 可预留用户标记 | 未来多用户时有用 |

### 借鉴的成熟产品

**Notion**
- ✅ Database 作为容器，Page 作为单元 → 对标 Bookshelf + Note
- ✅ 可按 Property 聚合和过滤 → 我们可借鉴 priority、urgency 过滤
- ✅ 模板概念 → 后期可加"新 Bookshelf"模板

**Obsidian + Vault**
- ✅ Vault（库）→ 对标 Bookshelf（容器）
- ✅ Note → Page
- ✅ 文件夹层级 → 我们简化为单层（一个 Note 不能在多个 Bookshelf）

**Evernote / OneNote**
- ✅ 笔记本 → Bookshelf
- ✅ 笔记 → Note
- ✅ Trash 笔记本 → 可选的"已删除"Bookshelf

**语雀 / Confluence**
- ✅ 知识库 → Bookshelf
- ✅ 文档 → Note
- ✅ 分享机制 → 预留 shared_with 字段

---

## 🎨 UI/UX 考量

### 1. 首页结构

**现在** → **改进后**
```
Orbit 页面
├─ 搜索 + 过滤
└─ 所有 Notes 列表

改为：

Orbit 页面（主导航）
├─ 标签页 1：我的便签（自由 Notes）
├─ 标签页 2：我的书橱（Bookshelf 列表）
├─ 标签页 3：最近打开（Bookshelf 和 Notes 混合）
└─ 标签页 4：归档（已删除或存档）
```

**收益**：
- 减少认知负担（不混乱）
- 自由 Notes 和组织的 Notes 分离
- 快速访问

### 2. Bookshelf 卡片设计

```
┌─────────────────────────────────────┐
│  ┌──────────────────────────────┐  │
│  │                              │  │  <- 封面图（高 120px）
│  │        [Cover Image]         │  │
│  └──────────────────────────────┘  │
│                                     │
│  📚 QuickLog                        │  <- 名称（可点击打开）
│  📌 优先级: ★★★ | 紧急: ★★★ | 📊 5  │  <- 元数据
│  📝 12 notes | Last update: 3h ago  │  <- 内容统计 + 更新时间
│                                     │
│  ⋮ (更多菜单) | 编辑 | 删除           │  <- 操作
└─────────────────────────────────────┘
```

**选项**：
- 卡片宽度：180-220px（最多 4 列）
- 封面优化：可上传自定义图片，或生成渐变色背景
- 悬停效果：显示最近 3 个 Notes 的缩略图

### 3. Bookshelf 详情页

```
┌─────────────────────────────────────────┐
│ ← 返回  QuickLog  [编辑] [设置] [⋮]    │  <- 顶部导航
├─────────────────────────────────────────┤
│                                         │
│        ┌──────────────────┐             │
│        │                  │             │
│        │   [Cover: 200px] │  优先级: ★★★  │  <- 左图右文
│        │                  │  紧急度: ★★★  │
│        │                  │  使用: 27      │
│        └──────────────────┘  📝 12 Notes  │
│                                         │
│        最后更新: 2025-10-31 12:34       │
├─────────────────────────────────────────┤
│  搜索 Notes │ 过滤 │ 排序 │ [+ 新增]    │  <- 工具栏
├─────────────────────────────────────────┤
│                                         │
│  [卡片视图] [列表视图]                   │  <- 视图切换
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Note 1 | Note 2 | Note 3 | ...  │   │  <- Notes 区域
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### 4. Note 卡片中显示 Bookshelf

```
改进前：

┌─────────────────────┐
│  Note Title         │
│  ───────────────────│
│  Preview text...    │
│  ───────────────────│
│  📌 Tag1 | Tag2     │
│  🕐 2025-10-31      │
└─────────────────────┘

改进后：

┌─────────────────────┐
│  📚 QuickLog        │  <- Bookshelf 标记（可点击跳转）
│  Note Title         │
│  ───────────────────│
│  Preview text...    │
│  ───────────────────│
│  📌 Tag1 | Tag2     │
│  🕐 2025-10-31      │
└─────────────────────┘
```

---

## 🔄 数据一致性考量

### 问题 1：note_count 冗余

**问题**：当 Note 添加/删除时，`bookshelf.note_count` 可能不同步

**解决方案**：
```python
# 方案 A：应用层保证一致（代码检查）
# 方案 B：后台任务定期同步
# 方案 C：视图计算（每次 SELECT 时计算）

# 推荐方案 AB 混合：
# - 应用层保证实时准确
# - 后台任务周期性审查（可告知用户"需要修复"）
```

### 问题 2：复制 Note 时的 Bookshelf 处理

**当前逻辑**：
```python
原 Note: bookshelf_id = "shelf_A"
    ↓ 复制
新 Note: bookshelf_id = "shelf_A"  ✓
```

**变化**：
- shelf_A.note_count += 1（需更新）

**前端提示**：
```
"✅ 已复制！新 Note 也加入 QuickLog 书橱"
```

### 问题 3：批量操作的事务性

**场景**：用户选择 10 个 Notes，转移到另一个 Bookshelf

```python
@db.transaction()  # 确保原子性
def bulk_move_notes(
    note_ids: List[str],
    source_shelf_id: str,
    target_shelf_id: str,
    db: Session,
):
    for note_id in note_ids:
        move_note_to_bookshelf(note_id, target_shelf_id, db)

    # 一次性更新计数
    source_shelf.note_count -= len(note_ids)
    target_shelf.note_count += len(note_ids)
    db.commit()
```

---

## 🎯 搜索和过滤考量

### 搜索优先级

```
1️⃣  全局搜索（从 /orbit 首页）
    ├─ 在所有 Notes 中搜索（bookshelf_id 无关）
    ├─ 在所有 Bookshelves 中搜索
    └─ 混合结果（优先显示 Bookshelf，再显示 Notes）

2️⃣  Bookshelf 内搜索（在 /orbit/bookshelves/[id]）
    ├─ 仅在该书橱的 Notes 中搜索
    └─ 支持"转移"操作
```

### 过滤维度

```
按 Bookshelf 过滤：
  ├─ 自由 Notes（bookshelf_id = NULL）
  ├─ 特定 Bookshelf
  └─ 已删除 Bookshelf 的 Notes

按 Note 属性 过滤：
  ├─ 优先级
  ├─ 紧急度
  ├─ 使用次数
  ├─ 创建时间
  ├─ 更新时间
  └─ 标签（现有功能）

按 Bookshelf 属性 过滤：
  ├─ 优先级
  ├─ 紧急度
  ├─ 使用次数
  ├─ Note 数量（> N）
  └─ 状态（active、archived）
```

---

## 📊 性能考量

### 查询优化

```sql
-- 获取 Bookshelf 及其 Notes（N+1 问题）
SELECT bs.*, COUNT(n.id) AS note_count
FROM orbit_bookshelves bs
LEFT JOIN orbit_notes n ON bs.id = n.bookshelf_id
GROUP BY bs.id
ORDER BY bs.created_at DESC
LIMIT 20;

-- 优化：不计算，直接用冗余字段
SELECT * FROM orbit_bookshelves
ORDER BY created_at DESC
LIMIT 20;
-- note_count 已存储，无需 JOIN
```

### 索引策略

```sql
-- 关键索引
CREATE INDEX idx_notes_bookshelf_created ON orbit_notes(bookshelf_id, created_at DESC);
CREATE INDEX idx_bookshelves_status_created ON orbit_bookshelves(status, created_at DESC);
CREATE INDEX idx_bookshelves_priority ON orbit_bookshelves(priority);
```

### 缓存策略

```typescript
// 缓存 Bookshelf 列表（变化较少）
queryKey: ["bookshelves"],
staleTime: 60_000,  // 60 秒过期

// 缓存单个 Bookshelf（变化偶发）
queryKey: ["bookshelf", id],
staleTime: 30_000,  // 30 秒过期

// Notes 缓存较激进（变化频繁）
queryKey: ["bookshelf", id, "notes"],
staleTime: 5_000,   // 5 秒过期
```

---

## 🛡️ 删除和恢复考量

### 方案：无硬删除策略

```sql
-- 方案 A：软删除
ALTER TABLE orbit_bookshelves
ADD COLUMN status TEXT DEFAULT 'active';
-- status: 'active' | 'archived' | 'deleted'

-- 恢复时只需：
UPDATE orbit_bookshelves SET status = 'active' WHERE id = '...';
```

### 垃圾桶 Bookshelf

```
特殊 Bookshelf：__Trash
  ├─ 系统自动创建
  ├─ 删除的 Notes 暂时放这里
  ├─ 支持定期清理（设置 30 天自动删除）
  └─ 用户可恢复
```

---

## 🔐 权限和共享考量（未来）

### 预留字段

```python
class OrbitBookshelf(Base):
    # ...
    created_by: UUID  # 创建者
    shared_with: List[UUID]  # 共享给谁
    permissions: str  # "view", "edit", "admin"
```

### 访问控制

```
私有：只有创建者能看
共享：can_view、can_edit、can_share
公开：可生成分享链接
```

---

## 📝 迁移计划细节

### Day 1：数据库和后端（无 UI 中断）
```python
# 1. 数据库迁移
python alembic upgrade head

# 2. 创建测试数据
bookshelf_service.create_bookshelf(name="QuickLog")

# 3. API 测试
pytest tests/bookshelf/test_api.py
```

### Day 2-3：前端集成
```typescript
// 1. 新增页面 /orbit/bookshelves
// 2. 在首页集成 Bookshelf 区域
// 3. 在 Note 卡片添加操作菜单
// 4. 测试所有流程
```

### Day 4：用户指引
```markdown
# 📚 新功能：书橱管理

现在你可以将 Notes 组织到书橱中：

1. 打开"我的书橱"
2. 创建新书橱（如 QuickLog）
3. 将现有 Notes 添加进去

✨ 提示：你现有的 Notes 仍然可用，无需迁移！
```

---

## 🎁 可选的高级功能

### 短期（可做）
- [ ] Bookshelf 封面图编辑（上传或生成）
- [ ] 书橱的排序（拖拽排序）
- [ ] 快捷搜索（`shelf:quicklog` 语法）
- [ ] 书橱模板（预设名称和标签）

### 中期（值得做）
- [ ] 书橱合并
- [ ] 书橱统计仪表板（Notes 数量趋势等）
- [ ] 自动分类（AI 推荐）
- [ ] 内容导出（整个 Bookshelf 导出为 PDF/ZIP）

### 长期（产品级）
- [ ] 多人协作（共享和权限）
- [ ] 版本历史
- [ ] 书橱分享链接
- [ ] 移动适配

---

## ✅ 最终检查清单

- [ ] 数据库设计无冗余问题
- [ ] 删除逻辑清晰（级联 vs 孤立）
- [ ] 复制逻辑完整（新 Note 落在原 Bookshelf）
- [ ] 转移逻辑安全（事务性）
- [ ] 搜索和过滤全面
- [ ] 性能指标合理（无 N+1）
- [ ] 缓存策略恰当
- [ ] UI 一致性检查
- [ ] 后端 API 完整
- [ ] 前端 Hook 齐全
- [ ] 测试覆盖关键路径

---

## 🤔 最后的思考

### 这个设计的强点
1. ✅ **与 Note 系统高度契合** — 不破坏现有功能
2. ✅ **渐进迁移** — 用户可选使用
3. ✅ **高内聚低耦合** — 容器和内容独立
4. ✅ **性能优先** — 冗余字段换取查询速度
5. ✅ **未来可扩展** — 预留多用户、共享等

### 可能的挑战
1. ⚠️ **数据一致性** — note_count 需要格外小心维护
2. ⚠️ **用户学习曲线** — 需要好的文档和引导
3. ⚠️ **迁移工作量** — 前后端都要改，但值得

### 建议的优化方向
- 不必一次性实现所有功能，分批推出
- 优先做 MVP，收集用户反馈再迭代
- 重点关注数据一致性（比功能完整性更重要）

---

## 📞 下一步

等待你的反馈：

1. ❓ 对这个方案满意吗？
2. ❓ 需要调整哪些地方？
3. ❓ 是否有新的需求没有覆盖？
4. ❓ 开始实现吗？（从哪一步开始？）

**我已准备好：**
- 📋 详细的数据库迁移脚本
- 🔧 后端 Service 完整代码
- 🎨 前端组件和 Hooks
- 📚 用户文档和操作指南
