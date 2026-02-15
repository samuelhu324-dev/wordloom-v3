# ADR-096: Bookshelf Dashboard Layout V2 & Library Overview List V3 (Plan48 Option B)

- Status: Accepted (Nov 25, 2025)
- Deciders: Wordloom Core Team
- Context: Plan48 Option B screenshots, VISUAL_RULES, DDD_RULES, HEXAGONAL_RULES
- Related: ADR-094 (Library Detail & Theme Integration), ADR-095 (Bookshelf Compact View Upgrade)

## Context

Bookshelf Dashboard（Library Detail 内）与 Admin → Libraries 列表长期存在列宽不足、操作列散落、封面尺寸不一致的问题。
Plan48 决策把 Bookshelf Dashboard 升级为 6 列 Layout V2，并要求 Libraries 列表复制相同节奏：左侧更大的封面 + 名称区，中间显式的说明与标签/指标区，右侧聚合时间戳与操作按钮。早期实现仅更新 Bookshelf 视图，Libraries 列表仍使用 32px 封面 + 混合列，导致视觉与交互脱节。

## Decision

1. **Bookshelf Dashboard Layout V2**：
   - 列顺序固定为 `cover → title → tags → status → metrics → actions`。
   - 操作列统一使用 IconButton（Edit / Pin / Archive / Delete），全部复用既有 UseCase；按钮 stopPropagation。
   - 64px cover + Library theme 渐变，health/status 文案依据 GetBookshelfDashboardUseCase DTO。

2. **Library Overview List Layout V3（Option B）**：
   - grid-template-columns: `360px 320px 280px 220px 120px`；允许宽度自适应但列顺序不可变。
   - 列 1（cover + name）：LibraryCoverAvatar size=96 + 名称 + pinned/archived 徽章；整列点击进入详情。
   - 列 2（description）：最多 3 行 clamp；空值显示“— 暂无说明”，禁止塞入按钮或指标。
   - 列 3（tags & metrics）：顶部 `LibraryTagsRow`（≤3），底部 metrics pill（bookshelves_count, books_count, last_activity_at, views_7d）。
   - 列 4（timestamps）：`创建：YYYY/MM/DD`、`更新：YYYY/MM/DD · x 天前`，ISO 数据来自 DTO 的 created_at/updated_at。
   - 列 5（actions）：Edit / Pin / Archive / Delete，沿用 Bookshelf Dashboard 的手势和 tooltip。
   - 所有列在焦点态/键盘导航保持 role="button" 行，IconButton stopPropagation。

3. **Documentation & Contract Sync**：VISUAL_RULES 新增 `library_overview_list_v3`，DDD_RULES/HEXAGONAL_RULES 记录对应策略，确保未来改动同步。

4. **Audit List Interaction Complete（Plan50）**：
   - 行节点统一 role="button" + tabIndex=0，行点击、Enter/Space、状态 pill 点击都走同一导航 handler，避免“只剩操作列可点”的状态。
   - Pin/Unpin、Archive/Restore、Delete 均通过既有 UseCase（UpdateBookshelfPin/Archive/Restore/Delete）发起，成功后统一 invalidate `['bookshelves_dashboard', libraryId]`。
   - 新增 `BookshelfTagEditDialog`，从 Dashboard 内直接更名与批量编辑标签，提交体 `{name, tags}` 交给 UpdateBookshelfUseCase；Tag 推荐从 `/api/v1/tags?scope=bookshelf` 获取。
   - Delete 操作沿用 Library 列表的 ConfirmDialog，确认文案复用“删除后不可恢复”条目，确保危险操作一致。

## Rationale

- Option B 方案带来更大封面与清晰的信息分区，提高扫读效率并与 Bookshelf Dashboard 统一视觉语言。
- 保持行动按钮一致可以减少维护多套交互逻辑的成本，并复用既有应用层端口。
- 将描述、标签、指标、时间戳拆分为独立列，使得每类信息有稳定的空间，避免混杂导致的视觉噪音。

## Scope

- Frontend：`frontend/src/features/library/ui/LibraryList.tsx`, `LibraryTagsRow`, `LibraryCoverAvatar`。
- Documentation：VISUAL_RULES, DDD_RULES, HEXAGONAL_RULES。
- 不涉及 Backend/Domain 字段新增；所有数据来自现有 LibraryOverview DTO。

## Non-Goals

- 不将封面或说明写入额外的领域字段；仍通过 DTO 派生。
- 不新增排序/过滤端点；继续使用现有 pinned+last_activity 逻辑。
- 不引入新操作类型或权限。

## UX / Layout Notes

- 96px Cover：圆角 12px，object-fit: cover，空态使用首字母渐变。
- Description：`display: -webkit-box` + `line-clamp: 3`；hover 不展开。
- Metrics：使用 `--wl-text-secondary` 颜色 + 👁📚 等 Lucide 图标，保持单行。
- Timestamp 列内以 12px 字体展示 `formatDate` + `formatRelative`。
- 行 hover 背景与 action 颜色沿用 Plan48 token。

## Implementation Notes

- 新增 `LIST_VIEW_COVER_SIZE = 96`、`descriptionClampStyle` 常量，grid 设置 `360px 320px 280px minmax(180px, 1fr) 120px`（根据视口调整）。
- `LibraryList` 中的 metrics 行使用 `LibraryMetricsRow` hooks，避免重复查询。
- 添加 `formatDate` 辅助函数确保时间戳一致。
- 文档同步：
  - VISUAL_RULES → `library_overview_list_v3` 段落。
  - DDD_RULES → `POLICY-LIBRARY-LIST-LAYOUT-V3`。
  - HEXAGONAL_RULES → `library_overview_list_v3_port`。
- `frontend/src/features/bookshelf/ui/BookshelfDashboardBoard.tsx` 负责创建 editingItem 状态并打开 `BookshelfTagEditDialog`；Dialog 内部使用 `useBookshelfQuickUpdate` hook（TanStack Query）提交 name/tags。
- `BookshelfDashboardCard.tsx` 把行点击、pill 点击、IconButton 触发拆分为 `handleOpen` 与 `handleAction`，并确保 aria-pressed/aria-label 按照 pinned/status 更新。
- Tag dialog 推荐列表来源 `useTagsSuggestions`（GET `/api/v1/tags?scope=bookshelf&limit=20&query=`），本地缓存 5 分钟，失败时显示 fallback chip。

## Testing

- Frontend：Storybook 场景 + Jest/Vitest snapshot（空描述/长描述/无标签/操作按钮 hover）。
- Playwright：验证点击封面/Enter 导航，点击操作不导航；Pin→Tag 编辑→Archive→Delete 顺序操作后列表保持一致，toast 与 refetch 正常。
- Backend Contract：`test_bookshelves_endpoint.py` / `test_bookshelf_dashboard_endpoint.py` 继续断言 DTO 字段齐全（含 tag_ids/tags_summary/pinned/status）。
- Dialog 单测：`BookshelfTagEditDialog.test.tsx` 覆盖输入校验、Tag 搜索、保存成功与失败的可视反馈。

## Rollback

- 可通过 git revert 恢复旧版布局；文档需同步回退以避免冲突。

## References

- Plan48 Option B mock (QuickLog / Image)
- VISUAL_RULES.yaml → `library_overview_list_v3`
- DDD_RULES.yaml → `POLICY-LIBRARY-LIST-LAYOUT-V3`
- HEXAGONAL_RULES.yaml → `library_overview_list_v3_port`
- frontend/src/features/library/ui/LibraryList.tsx
