# ADR-111: Book Maturity Coverage & Timeline Integration

- Status: Accepted (Nov 28, 2025)
- Deciders: Wordloom Core Team
- Context: Plan72 (书籍成熟度 / COVERAGE)、Plan86 (Chronicle 时间线)、Plan88/Plan89/Plan90 (封面 Lucide icon + 展柜视图)
- Related: ADR-092 (Book maturity segmentation), ADR-093 (Chronicle timeline API), ADR-099 (Book workspace tabs), ADR-110 (Book cover Lucide icons), DDD_RULES `POLICY-BOOK-MATURITY-*` & `POLICY-BOOK-CHRONICLE-BOUNDARY`, HEXAGONAL_RULES `book_maturity_coverage_ports` & `chronicle_timeline_strategy`, VISUAL_RULES `book_maturity_view_v2` / `book_workspace_tabs_visual_rules`

## Problem

分散的文档与实现导致“成熟度 → COVERAGE → 时间线 → 封面 icon”之间缺乏统一叙述：

1. **成熟度覆盖率**：Bookshelf Detail 页的 SummaryBar 早已显示 COVERAGE，但公式与数据来源只在 UI 代码中存在，DDD/Hex 文档未同步，导致 Review 无据可依。
2. **Todo/Chronicle 关系**：成熟度 state machine 依赖 Todo 投影与 Chronicle 事件，但 Domain vs Hex vs Visual 的责任边界不清（例如：是否允许在 Book DTO 中返回最近事件？）。
3. **Book Workspace**：Overview / Blocks / Timeline tabs 已整合（Plan56），但 Timeline 入口、Block Debug 视图、BookMainWidget 之间的端口依赖尚未写入 ADR。
4. **封面 icon + New Book 流程**：BookEditDialog 现在既能编辑也能创建书籍，并附带 Lucide icon 选择器，但 Hex / DDD / Visual 只有局部说明，没有一份统一决策确保“单 PATCH + 受控字段”原则在 create 流程同样成立。

## Decision

1. **公式与分层**：覆盖率固定为 `coverage = stable_count / max(1, total - legacy_count)`；Domain 仅输出原子计数，UI helper（`buildBookMaturitySnapshot`）负责计算百分比并渲染 SummaryBar。
2. **Todo / Timeline 边界**：Todo 投影仍由 Block 内容派生，应用层在 `UpdateBookMaturityUseCase` 中调用 TodoProjectionService 判断 `open_todos`；Chronicle 事件保持独立聚合，只通过 `/api/v1/chronicle/books/{bookId}/events` 暴露，只读、分页、可过滤。
3. **Book Workspace / Timeline 集成**：`/admin/books/{bookId}` 作为唯一工作区，Overview Tab 展示最近事件（timeline summary）、Blocks Tab 使用 Inline 编辑、Timeline Tab 完整展示 Chronicle；Block Debug 页仅面向 QA，并明确 “Debug Only”。
4. **共享 BookEditDialog**：`BookEditDialog` 支持 `mode='edit'|'create'`，create 流程由 BookMainWidget 的 `+NEW BOOK` 按钮触发；封面 icon（cover_icon）与标签（tag_ids）继续借由单次 mutate（必要时后台二次 PATCH）更新，字段与 Domain/Hex 契约一致。

## Partition Migration & Timeline Coupling (Plan92)

- **单一事实源**：`Book.maturity` 字段即 Bookshelf 分区所依据的实时值；任何自动/手动的成熟度变化都必须先更新聚合，再由列表/Query DTO 读取，不允许前端估算。
- **迁移流水线**：`RecalculateBookMaturityUseCase` 与 `UpdateBookMaturityUseCase` 都会输出 `PartitionMigrationResult {book_id, from, to, score, is_manual_override, trigger}`，交给 PartitionMigrationNotifier（用于 UI cache）和 ChronicleRecorder（写 `stage_changed` 事件）。
- **时间线契约**：`stage_changed` 事件 payload 需包含 `from`, `to`, `maturity_score`, `manual_override`, `trigger_reason`，以便 Timeline Tab/Overview tooltip 展示卡片搬家缘由。未发生分区变化时禁止写事件，避免噪声。
- **Legacy 优先级**：当 `legacy_flag=true` 时，PartitionMigrationResult 强制输出 `to='legacy'`，并写入额外事件 `legacy_flag_changed`。恢复 Legacy 会触发反向迁移 + `stage_changed`。Legacy 区不计入 COVERAGE 分母，但 timeline 仍完整记录。
- **UI 反馈**：BookMainWidget 在收到 UpdateBookMaturity API 响应后立即移动卡片，并在 React Query invalidate 后与服务端结果对齐；Book Workspace Timeline Tab 默认不展示 `book_opened`，但 `stage_changed` 始终出现且携带 from→to + flash icon（若手动覆盖）。

## Domain Model Impact

- `Book` 聚合：
  - 字段：`maturity`, `maturity_score`, `is_legacy`, `cover_icon`, `bookshelf_id`, `library_id`, `latest_activity_at?`；不缓存 Todo 列表与 Timeline 记录。
  - 状态机：Seed → Growing → Stable → Legacy（Legacy 可通过 restore 回 Stable）；`maturity_score` ≥70 且 `open_todos==0` 才允许 Promote 到 Stable（开关 `enforce_stable_requires_zero_todo` 控制）。
  - COVERAGE：Domain 只负责给 ListBooksUseCase / GetBooksByBookshelfUseCase 提供 maturity + is_legacy；不写入 coverage 百分比。
- `Chronicle` 聚合：捕捉 book_* / block_* / todo_item_* 事件；Book DTO 仅可带 `latest_activity_at`（可选），不得附带事件数组。
- `Tag` 聚合：继续通过 BookTagSyncService 批量同步 `tag_ids`，仅返回 `tags_summary[]` 供 UI Ribbon 使用。

## Ports & Adapters

- **Inbound UseCases**
  - `ListBooksUseCase` / `GetBooksByBookshelfUseCase`: 返回 Pagination V2，items 内含 maturity/is_legacy/tags_summary/cover_icon；可选 meta.counts 用于 UI 统计。
  - `UpdateBookMaturityUseCase`: 调用 TodoProjectionService 验证 open_todos，再写入 maturity + 触发 Chronicle。
  - `UpdateBookUseCase` / `CreateBookUseCase`: 接受 title/summary/tag_ids/cover_icon（create 暂分两步：创建 → PATCH tag_ids）。
  - `ChronicleQueryService.list_book_events`: 提供时间线数据；Blocks Debug 页可复用 `list_block_events`。
- **Frontend Adapters**
  - `buildBookMaturitySnapshot(books)`：在 BookMainWidget 内按 maturity 分组 + 计算 coverage。
  - `BookMaturityView`：展示 SummaryBar、分区、viewMode 切换；`BookMainWidgetHeader` 管理 +NEW BOOK 按钮。
  - `BookEditDialog`：模式化对话框 + CoverIconPicker + TagSelector；`onPendingChange` 将 mutation 状态反馈给触发按钮。
  - `useChronicleTimeline(bookId, filters)`：Book Workspace Overview（summary）与 Timeline tab 共用；Block Debug 入口可传 blockId。

## UI / Interaction

1. **BookMainWidget**
   - SummaryBar 顶部显示 COVERAGE 百分比 + seed/growing/stable/legacy + total pill；view toggles（展柜/条目）互斥，按钮使用 aria-pressed。
   - `+NEW BOOK` 按钮打开 BookEditDialog (mode='create')，按钮在 mutation pending 时禁用，文案切换为“取消”以脱离对话框。
   - 展柜模式使用 BookShowcaseItem（卡片 + Lucide icon + 标签 ribbon + maturity pill）；条目模式使用 BookRowCard。

2. **BookEditDialog v3**
   - 统一标题栏，无副标题；字段顺序：Title → Summary → Cover icon → Tags。
   - mode='create'：提交 `{bookshelf_id,library_id,title,summary?,cover_icon?}`，若 tags 需二次 PATCH 也由同一 Dialog 控制 loading；成功后 toast“已创建书籍”。
   - mode='edit'：提交 `{title?, summary?, tag_ids?, cover_icon?}`；成功后立即刷新列表/详情。

3. **Book Workspace Tabs**
   - Hero 卡显示书籍基本信息 + 单书 COVERAGE 条（0-100%）。
   - Overview Tab 左列包含 timeline summary（最近 ≤5 条 Chronicle 事件），右列 InfoPanel 列出 library/bookshelf/ID/Timestamps。
   - Blocks Tab 继续使用 InlineCreateBar + BlockList + BlockEditor；Basement/Legacy 只读。
   - Timeline Tab 渲染 ChronicleTimelineList（分页 + chips 过滤），默认隐藏 book_opened；Block 写操作后仅 invalidate timeline query。

4. **Block Internal Timeline (Debug)**
   - `/admin/blocks` 入口仅为 QA 使用；右列展示紧凑时间线，顶部 chips 控制 event_types；Banner 标注“Debug Only”。

## Alternatives Considered

1. **把 COVERAGE 下沉到 Domain/Repository**：会迫使后端在查询阶段聚合 maturity 分布，破坏“平面列表 + UI 自行分组”的契约，并增加分页一致性问题，因此放弃。
2. **在 Book DTO 中附带最近 Chronicle 事件**：会导致 Book 聚合感知时间线细节，且响应体巨大；转而使用独立 Query Port + Timeline hook。
3. **为 New Book 保留旧的 inline 表单**：虽可避免 Modal，但难以复用 BookEditDialog v3 的封面 icon / Tag 逻辑，且破坏“编辑/创建共用”目标，故用共享 Dialog 取代。
4. **Timeline 嵌入 Block Tab**：会让 Block 编辑区域过度拥挤、难以聚焦；改为 Overview 摘要 + 独立 Timeline tab。

## Consequences

- **Positive**
  - COVERAGE、Timeline、BookMainWidget、BookEditDialog 共用一套规则，审查和回归测试有据可循。
  - UI/Domain 边界清晰：Domain 仅维护 maturity/score/event 发布；Application/Adapters 负责统计与渲染逻辑。
  - Book Workspace 与 Bookshelf 视图共享 chronicle hook，减少重复实现。
- **Negative**
  - BookMainWidget 重构需要额外的组件拆分（Header / View / Dialog 管理），短期内文件 diff 较大。
  - create 模式仍需二次 PATCH 才能附加标签（历史限制），需在后续迭代整合。
  - Timeline hook 需新增过滤芯片/分页 UI，带来额外测试负担。

## Implementation Notes

1. **Rules 文件同步**：
   - DDD_RULES：新增 `POLICY-BOOK-MATURITY-COVERAGE-VIEW`、扩充 `POLICY-BOOK-MATURITY-TODO-GATE`、`POLICY-BOOK-CHRONICLE-BOUNDARY` 等条目；明确 cover_icon 与成熟度/标签解耦。
   - HEXAGONAL_RULES：新增 `book_maturity_coverage_ports`、更新 `book_cover_icon_contract`、`chronicle_timeline_strategy`、`book_workspace_tabs_integration`，强调应用层端口职责。
   - VISUAL_RULES：记录 `book_maturity_view_v2`、`book_edit_dialog_v3` 新布局、Book Workspace hero coverage、Chronicle/Block timeline 视图。
2. **Frontend 结构**：
   - 拆分 `BookMainWidget`（Header/MaturityContainer/Dialog state）与 `BookEditDialog`（FormCore/TagSelector/CoverIconPicker）以降低复杂度。
   - `BookWorkspaceHeroCard` / `BookTimelinePanel` / `BookBlocksPanel` 作为独立组件，保持 FSD 层次。
3. **Testing**：
   - Backend：`test_books_endpoint.py` 覆盖 cover_icon + tag_ids；`test_chronicle_router.py` 验证 event_types 过滤。
   - Frontend：BookMainWidget viewMode + Dialog 流程快照/交互；BookWorkspace tabs E2E；Chronicle Timeline hook pagination。

## Future Work

- 合并 create + tag PATCH：在后端支持 create 时直接写入 tag_ids，减少额外请求。
- 替换 Block Debug Timeline：引入统一 UI 组件，并考虑权限控制与开关。
- 研究用 `counts` meta 直接由 API 返回 seed/growing/stable/legacy totals，减少前端重复统计成本（保持平面列表作为主数据源）。
- 将 COVERAGE 指标扩展到 Library / Workspace Dashboard，使 Library detail 能统一展示“成熟度进度”。
