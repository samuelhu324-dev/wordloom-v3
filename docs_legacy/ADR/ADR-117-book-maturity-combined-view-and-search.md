# ADR-117: Book Maturity Combined View & Search Toolbar

- Status: Accepted (Nov 30, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-096 (Library dashboard layout V2), ADR-110 (Book cover Lucide icons), ADR-116 (Pin visual sync), DDD_RULES `POLICY-BOOK-MATURITY-COMBINED-VIEW-FILTER`, HEXAGONAL_RULES `book_maturity_combined_view_filters`, VISUAL_RULES `book_maturity_combined_filter_bar`
- Related Artifacts: `frontend/src/widgets/book/BookMainWidget.tsx`, `frontend/src/widgets/book/components/BookMaturityFilterBar.tsx`, `frontend/src/features/book/model/useBooks.ts`, `backend/api/app/modules/search`

## Problem

1. Bookshelf → BookMainWidget 只能按 Seed/Growing/Stable/Legacy 四段依序展示，运营人员需要“把 Stable 放在最前”或“只看 Seed + Growing”以便集中整治，但目前必须滚动查看，效率低下。
2. Library Dashboard 已有成熟的工具条（筛选 + 搜索），Book 页面缺少类似能力，导致体验割裂，也无法快速定位指定书籍。
3. 现有搜索栏仅作用于 Library/Bookshelf，不支持在书籍上下文内搜索标题/简介/标签，更无法切换到全局 Search 模组。
4. 缺乏文档约束，容易出现“后端分段查询”或“新写 Search 端口”等偏离 DDD/Hexagonal 的实现。

## Decision

1. **保持单一数据源。** BookMainWidget 仍通过 `ListBooksUseCase` 获取完整分页数据 + `meta.counts`，UI 在客户端根据 maturity 字段重排/折叠，后端不接受任何新的筛选参数。
2. **新增 FilterBar 组件。** `BookMaturityFilterBar` 提供四类控件：阶段开关、顺序下拉、置顶优先 toggle、搜索输入。控件状态保存在本地 store + `localStorage('wl.bookList.filters')`，刷新后恢复，且不会写入 Domain。
3. **两段式搜索。** 默认 Local 模式在当前 Query cache 内匹配标题/简介/说明/标签；当用户切换到 Global 或输入≥3字符并点击“搜索全部”，前端改为调用 Search 模块 `/search/books` 端口并展示独立结果面板。Search 模块的索引字段扩充为 summary/description/tags_summary/maturity/bookshelf_name。
4. **结果呈现。** Local 搜索仅过滤现有卡片；Global 搜索在工具条下方显示 Result Sheet（至多 5 条），点击条目跳往书籍详情或滚动到现有卡片，绝不把 search hits 混入 TanStack Query 缓存。
5. **规则同步。** DDD_RULES、HEXAGONAL_RULES、VISUAL_RULES 分别记录 Domain 契约（无新端口）、端口/索引职责、UI 布局，可防止后续改动绕开治理。

## Consequences

- **正面：** 运营可在一个页面内完成“先看 Stable”或“只看 Seed & Growing”的聚焦操作，再辅以关键字搜索，大幅减少滚动与跳转。
- **正面：** Search 模块复用，避免为书籍列表额外造端口；索引扩展后也可服务其他上下文（例如 Book detail 搜索）。“Local→Global”切换让用户清楚数据来源。
- **负面：** 工具条引入更多本地状态，需要在 Zustand/Query 之间同步，增加测试矩阵。Global 搜索依赖 Search 服务，若索引落后会出现“结果找不到”的风险，需要 EventBus 监测。
- **负面：** 前端需维护 highlight、result sheet、筛选持久化等 UI 细节，初期实现成本较高。

## Implementation Notes

1. **Frontend:**
   - `BookMaturityFilterBar` 挂在 `BookMainWidget` header 下方，使用 12 列 Grid 与 Library Dashboard 对齐。状态集中在 `useBookFiltersStore`（Zustand）。
   - Local 搜索通过 memoized selector 过滤 Query cache；Global 模式调用 `searchBooks({ text, bookshelfId })` 并渲染 `SearchResultSheet` 组件。
   - Highlight 使用 `<mark>` 包裹匹配字符串；当筛选导致所有 Section 隐藏时，自动恢复 Stable 并展示提示。
2. **Backend/Search:**
   - `search_index` builder 纳入 summary/description/tags_summary/maturity/bookshelf_name 字段，触发源为 BookUpdated、BookTagSynced、BookMaturityChanged 事件。现有 Search API 契约不变，仅额外返回 bookshelf_name、maturity。
   - Search hits 结构 `{book_id,title,snippet,score,maturity,bookshelf_name,path}`；path 指向 `/admin/books/{id}`。
3. **Caching & Telemetry:**
   - Filter state写入 `localStorage('wl.bookList.filters')`，并在 `useEffect` 初始化后同步至 Zustand。记录 `analytics.book_filters_changed`、`analytics.book_search_global` 事件，便于衡量使用率。
4. **Testing:**
   - RTL 覆盖筛选、排序、Pinned toggle、Local/Global 搜索 + 结果点击。Playwright 验证筛选持久化与 result sheet 跳转。Backend Search 契约测试新增字段断言。
5. **Rollout Plan:**
   - Phase 0：上线 FilterBar + Local 搜索。
   - Phase 1：启用 Global 搜索与 Search API；默认 scope 仍为 Local。
   - Phase 2：根据遥测决定是否把 Global 设为默认或添加服务器端分页联动。
