# ADR-072: Basement UX & Restore Flows (Library Pre-View Panel)

Status: Proposed → Amended (2025-11-18)
Supersedes: Clarifies ADR-002 (Basement Pattern), extends ADR-071 (Multi-Library + Flat Endpoints + Page Isolation)
Related: ADR-008, ADR-009, ADR-010, ADR-013, ADR-014, ADR-016, ADR-017
Authors: Architecture Team
Reviewers: Product, UX, Backend, Frontend

---
## 1. 背景 (Context)
多 Library 能力已经通过 ADR-071 和数据库索引实现。现有 Basement 模式（软删除转移）已在 Domain + UseCase 层运行：
- Library 创建自动生成 Basement Bookshelf (RULE-010)
- Bookshelf 删除时其 Books 软删除并转入 Basement (Cascade)
- Book 删除采用 move_to_basement() (RULE-012)；恢复采用 restore_from_basement() (RULE-013)
现阶段缺失一个可视化、可操作且高效的“Basement 回收站体验”，并对恢复流程的边界（原书架存在与否、多 Library 场景、一键批量恢复/清理）进行统一定义。

## 2. 问题 (Problem)
1. 用户无法直观区分被删除的书籍其原书架当前是否仍存在。
2. 整架删除与部分书删除的视觉表现未定义。
3. 恢复书籍时缺乏决策支持（原书架存在：恢复到原书架还是迁移到新书架）。
4. 缺乏批量操作与滞留时间策略，回收站可能无限增长。
5. 前端目前只提供 type NORMAL|BASEMENT；缺少分组数据结构 (bookshelf_exists flag)。
6. 扁平路由策略下需要定义 Basement 相关端点的参数与响应 shape。

## 3. 目标 (Goals)
- G1: 在 Library 详情“前置界面”提供高效回收站面板（方案A 固定侧面板）。
- G2: 分组结构：按 Bookshelf 分组；提供 bookshelf_exists 标记。
- G3: 视觉区分：整架已删除 → 实体色；书架仍存在但部分书被删除 → 灰度半透明。
- G4: 恢复交互：书籍恢复支持原书架与新书架二选一；原书架缺失时强制选现存书架。整架恢复一并恢复内部书。
- G5: 支持批量恢复 / 批量清空（软删除永久清除二次确认）。
- G6: API 统一 `{items,total}` 列表形态；枚举小写；传输层与 UI 层大小写映射在适配层完成。
- G7: 可扩展：未来全局 `/admin/basement` 总览；滞留策略（默认 30 天）。

## 4. 决策 (Decision)
1. 改进：视觉模型调整——Basement 在 `/admin/libraries` 列表中以“单个虚拟 Library 卡片”方式出现（Card 标题建议："Basement 回收站"），与真实 Library 并列显示但拥有 `locked` 标记：
  - 不能被删除 / 重命名 / 进入常规编辑；点击跳转到 `/admin/basement` 全局回收站视图。
  - 该卡片并不映射真实 `Library` 聚合根；仅在前端通过虚拟 DTO 包装底层多库 Basement 数据汇总。
  - 仍保留每 Library 的 Basement Bookshelf 机制（领域不变），UI 汇总统计 deleted bookshelves / books 总量。
  原先的“每Library详情右侧固定 Panel”模式降级为 Phase 2 备选增强（在 `/admin/libraries/[id]` 详情中仍可加速恢复）。
2. 分组 DTO 定义：`BasementGroupDto { bookshelf_id, name, bookshelf_exists: bool, count: int, items: DeletedBookDto[] }`。
3. API 新/巩固端点（扁平，不嵌套）：
   - GET `/books/deleted?library_id={uuid}&offset=&limit=&bookshelf_id=&q=` → `{items: BasementGroupDto[], total}` (分页针对组或书籍视图，策略：对 books 分组后总数 = 组内书总数)。
   - POST `/books/{book_id}/restore` Body: `{ target_bookshelf_id?: UUID }` Query: `mode=original|new`；响应包含 `{restored_to, original_bookshelf_exists, original_bookshelf_id?}`。
   - GET `/bookshelves/deleted?library_id={uuid}` → 已删除 Bookshelf 列表（含每架 book 计数）。
   - POST `/bookshelves/{id}/restore?with_books=true|false` → 恢复书架及内部书（默认 with_books=true）。
   - DELETE `/libraries/{id}` → Library soft-delete (cascade to Basement)。
   - POST `/libraries/{id}/restore?mode=library_only|with_children` → 恢复策略。
4. 恢复逻辑：
   - 若书原书架存在：默认建议恢复到原书架；用户可选“迁移到其他书架”。
   - 若原书架不存在：必须选择现存书架；若没有书架 → 提示先创建书架。
   - 整架恢复：对 Bookshelf 及其 Books 逐一调用恢复域方法（事务包裹）。
5. 视觉规则：
   - Entity Color（品牌主色/可主题化）= 书架已删除（组处于“孤立”状态）。
   - Grayscale / 40% opacity = 书架仍存在；强调书仅被删除。
   - 选中态加 2px 内发光+提升 z-index；批量模式下显示复选框角标。
6. 商业级组件美化规范：在 VISUAL_RULES 增补（见 §9）。
7. 不引入跨 Library 恢复（保持聚合边界清晰）；后续可在 ADR 中再扩展跨库迁移能力。
8. 数据保留策略：默认 30 天；超过后进入“过期”状态（可以批量永久清理）。策略参数后续存储于配置表。
9. 审计：恢复 & 永久清理写入 AuditLog（operation, actor, target_ids, timestamp）。

## 5. 非目标 (Non-Goals)
- 不提供块级 (Block) Basement UI（Block 恢复仍在 Book 编辑器内）。
- 不实现跨 Library 批量迁移。
- 不实现版本回溯或差异对比（单纯软删除恢复）。

## 6. 风险 (Risks)
| 风险 | 影响 | 缓解 |
|------|------|------|
| 分组查询性能 | 大量删除书籍导致分页复杂 | 添加 `books.soft_deleted_at` + `bookshelf_id` 组合索引；预取书架存在性 |
| 恢复冲突 (同名书架) | 用户恢复后产生命名冲突 | 恢复前校验，若冲突 → 推荐重命名流程 |
| UI 复杂度增加 | 初次使用认知负担 | 提供空状态引导 + Tooltips + 快捷恢复按钮 |
| 大批量恢复长事务 | 锁表/延迟 | 分批提交 (chunk 200) + 后台任务队列（Phase B） |

## 7. 备选方案 (Alternatives)
- Tab 切换形式（Basement 与正常视图分离）→ 降低同时对比效率，放弃。
- 单列表混合标记删除状态 → 视觉噪音高，恢复路径不明确。

## 8. 详细设计 (Detailed Design)
### 8.1 数据模型扩展
DeletedBookDto: `{ book_id, title, deleted_at, original_bookshelf_id, original_bookshelf_name?, size?, author?, tag_ids? }`
BasementGroupDto: `{ bookshelf_id, name, bookshelf_exists, count, items: DeletedBookDto[] }`
LibraryDto 扩展：`basement_bookshelf_id`（已存在）；新增可选 `deleted_at` 标记软删除状态。

### 8.2 后端实现要点
- Repository: `get_deleted_books(library_id, filters)` 返回书 + 原书架 ID；再二次查询所有涉及的 `bookshelf_id` 存在性集合。
- UseCase: ListBasementBooksUseCase 增强分组逻辑：
  1. 查询软删除 Books  (soft_deleted_at != NULL && library_id=...)
  2. 计算 grouping key = original_bookshelf_id
  3. bookshelf_exists = 原书架是否仍存在 (set membership)
  4. 构造 DTO 列表并排序：先“整架已删除”(exists=false)、再按最新 deleted_at 降序。
- 恢复：RestoreBookUseCase 增加分支：若请求不提供 target_bookshelf_id 且原书架存在 → 恢复到原书架；否则要求提供 target_bookshelf_id。
- 事务：整架/整库恢复采用单事务；批量恢复 chunk 方案预留。

### 8.3 API 契约示例
GET /books/deleted?library_id=...
Response 200:
```json
{
  "items": [
    {
      "bookshelf_id": "uuid-1",
      "name": "Programming",
      "bookshelf_exists": true,
      "count": 3,
      "items": [
        {"book_id": "b1", "title": "Rust", "deleted_at": "2025-11-18T10:21:00Z", "original_bookshelf_id": "uuid-1"},
        {"book_id": "b2", "title": "Go",   "deleted_at": "2025-11-18T10:22:00Z", "original_bookshelf_id": "uuid-1"}
      ]
    },
    {
      "bookshelf_id": "uuid-2",
      "name": "Design Patterns",
      "bookshelf_exists": false,
      "count": 5,
      "items": [ ... ]
    }
  ],
  "total": 8,
  "message": "Basement groups loaded"
}
```

POST /books/{id}/restore
Body `{ "target_bookshelf_id": "uuid-1" }`
Response 200:
```json
{ "book_id": "b2", "restored_to": "uuid-1", "original_bookshelf_id": "uuid-1", "original_bookshelf_exists": true }
```

### 8.4 前端 FSD 映射
Layers:
新视觉策略引入“虚拟库”层：
- entities: `basement.ts` 定义 DTO & mapper (`VirtualBasementLibraryDto`：`id:"__BASEMENT__" | name:"Basement" | locked:true | stats{deleted_books, deleted_bookshelves}`)
- features: `useVirtualBasementLibrary()`（在 libraries 列表查询后追加虚拟卡片）、`useBasementGroups(libraryId?)`（libraryId 可选；缺省表示全局汇总）
- widgets: `BasementLibraryCard`（显示总删除数量与入口按钮）、`BasementGroupCard`、`RestoreBookModal`、`BulkActionsBar`
- pages: `/admin/libraries`（列表含虚拟卡片）、`/admin/basement`（全局回收站主页面）、`/admin/libraries/[id]`（Phase 2 可选：侧边 Panel 增强）

### 8.5 交互与状态
- 初始加载 Skeleton 组卡片；错误 → Toast + 重试按钮。
- 分组折叠/展开（记忆状态 localStorage）。
- 批量模式：进入后卡片切换为多选，显示顶栏批量恢复按钮。
- 清空操作：二次确认 Modal（输入库名或"CLEAR"）。

### 8.6 无障碍 (A11y)
- 卡片 `role="group"`；折叠按钮使用 `aria-expanded`。
- 恢复按钮具备 `aria-label="恢复书籍 {title}"`。
- 键盘导航：上下切组、左右切书、Enter 操作恢复。

### 8.7 性能
- 分页默认 limit=20 组；组内书上限（溢出显示“+N more”链接跳转二级 Modal ）。
- useBasementGroups 缓存 key: `['basement','groups',libraryId, filters]`，staleTime = 30s。
- 预取：当用户展开组时预取其余书籍详情（tags, cover）。

### 8.8 审计 & 监控
- 事件：`basement.restore.book`, `basement.restore.bookshelf`, `basement.clear`, `basement.delete.permanent`.
- 指标：恢复次数、平均恢复延迟、过期清理数量。

### 8.9 商业级 UI 设计（Elegant / Commercial）
| 元素 | 规范 |
|------|------|
| 主色 | 使用主题变量 `--accent`；Basement 实体色卡提升饱和度 + subtle gradient |
| 灰度卡 | `background: var(--surface-subdued); opacity: .6; backdrop-filter: blur(2px)` |
| 按钮尺寸 | 基础高度 36px；主操作（恢复/批量恢复）> 44px with icon + label |
| 圆角 | 卡片 12px；按钮 8px；Modal 20px（与现有 tokens.css 对齐） |
| 阴影 | Elevation 1: `0 2px 4px rgba(0,0,0,.08)`；Hover: elevation 2；选中：内发光 `0 0 0 2px var(--accent-alpha)` |
| 动效 | 展开折叠：`height` + `opacity` 动画 160ms cubic-bezier(.4,.0,.2,1)；批量模式淡入选择框 |
| 图标 | 使用现有 icon 集：trash, restore, check-circle, layers, recycle |
| 颜色语义 | 恢复成功 Toast: accent; 清空警告: danger + subtle red background |
| 适配暗色 | 仅调整阴影透明度、gradient 角度保持；不改变语义色饱和度过多 |
| 空状态 | 插画 + 文案：“暂无已删除内容，继续创作吧” + 直接创建书按钮 |

### 8.10 滞留策略 (Retention)
- 字段：`deleted_at`；过期判断 = `now() - deleted_at > retention_days`。
- 后端计划任务（Phase B）：每日扫描过期项 → 标记 `expired=true`；UI 过滤显示“即将清除”。
- 配置：`retention_days` 默认 30；DB 配置表 + 环境变量覆盖。

## 9. 实施步骤 (Implementation Steps)
### Phase 1 (当前迭代)
1. 增强 ListBasementBooksUseCase → 分组 + bookshelf_exists。
2. 新增 DeletedBookshelf 端点 & UseCase。
3. RestoreBookUseCase 支持默认原书架恢复与目标书架选择。
4. API Router 更新 + 文档同步 (OpenAPI tags: basement)。
5. 前端 DTO / Hooks / Panel 初版（不含 retention UI）。
6. 更新 DDD_RULES.yaml / HEXAGONAL_RULES.yaml / VISUAL_RULES.yaml 增补 Basement UX 规则。
7. ADR-072 合并。

### Phase 2
1. 批量恢复 API + Hooks。
2. 清空回收站 (permanent delete) + 审计记录。
3. Retention 过期标记与 UI 提醒。
4. 全局 /admin/basement 视图（跨库汇总）。

### Phase 3
1. 性能优化：组缓存、数据库索引 (soft_deleted_at, library_id)。
2. 后台任务队列处理大批量恢复。
3. 跨库迁移（新 ADR）。

## 10. 验证 (Validation)
- 单测：UseCase 分组逻辑、恢复分支、书架存在性判断。
- 集成测试：删除→列表→恢复→再次列表为空。
- E2E：用户流程（删除书架、删除书、批量恢复、清空）。
- 性能：大数据基准 (10k deleted books) 下响应 < 400ms（后端预聚合）。

## 11. 后果 (Consequences)
正面：提高恢复效率与透明度；减少误删恐惧；统一软删除语义。
负面：引入额外复杂度与索引；需要更多测试维护；面板在小屏占空间。
缓解：渐进式加载、Skeleton、移动端改 Tab。

## 12. 迁移 (Migration)
- 现有删除记录直接被新分组逻辑消费（无需数据迁移）。
- 添加必要索引：`CREATE INDEX idx_books_soft_deleted ON books (library_id, soft_deleted_at) WHERE soft_deleted_at IS NOT NULL;`。
- 添加可选 retention 配置表 `system_settings (key,value)`。

## 13. 开发者笔记 (Developer Notes)
- 不要在 Domain 层加入展示字段（如 bookshelf_exists）；此为 UseCase 聚合/Presenter 逻辑。
- 前端避免在组件内直接判断枚举传输值；使用 mapper。
- 批量恢复初版以串行实现，后续再并行。

## 14. 中文执行摘要 (Chinese Summary)
本决策修订：Basement 以“单个虚拟 Library 卡片”形式出现在 `/admin/libraries`，不可删除重命名，仅作为全局回收站入口；点击进入 `/admin/basement` 进行按书架分组的软删除内容管理。领域仍维持“每 Library 具有 Basement Bookshelf”机制，不创建真实 Library 聚合。分组依据原书架 ID，展示书架是否仍存在（整架删除→实体色；书架仍存在→灰度）。恢复书籍时，原书架存在默认回原书架，可选迁移；原书架缺失需选目标书架。接口继续扩展分组/已删除书架/恢复端点，统一 `{items,total}` 响应与枚举小写传输，并增加虚拟库统计 DTO。商业级 UI 风格与保留期策略（30 天）保持不变，原“库详情右侧固定 Panel”降级为后续增强。该修订驱动 FSD 新增 `VirtualBasementLibraryDto` 与 `BasementLibraryCard` 组件及相应 Hooks，并同步更新三大 RULES 文件。

---
END OF ADR-072
