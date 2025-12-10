Book 页面 i18n 计划（简版）

目标：让 /admin/bookshelves/[id] 中的 BookMainWidget、成熟度面板、搜索/过滤、陈列区、操作 toast/确认弹窗在中英文间实时切换，与现有 bookshelves.* 规范保持一致。
策略：新增 books.* 字典命名空间，逐个组件接入 useI18n()，替换所有硬编码文本（含 aria/tooltip/toast），并复用 locale 感知的时间/计数文案。
步骤

梳理文案来源：逐个标记 BookMainWidget.tsx、main-widget/*.tsx（Header、FilterBar、SearchBar、maturity hooks）、BookshelfBooksSection.tsx、features/book/ui/BookDisplayCabinet.tsx 与书籍相关 toast/confirm，列出需抽取的中文/英文字符串与动态变量（计数、书名、成熟度、搜索关键字等）。
扩展字典：在 zh-CN.ts 与 en-US.ts 中新增 books.* key（例如 books.header.heading, books.header.toggle.grid, books.filters.mode.combined, books.section.seed.empty, books.toast.moveToBasementSuccess 等），并按模块分组，确保 aria/tooltip/按钮/toast/错误文案都有对应条目。
接入 useI18n：给 BookMainWidget 及其子组件（Header、FilterBar、SearchBar、BookshelfBooksSection、ErrorBoundary fallback、BookMaturityView props、BookDisplayCabinet 交互提示）引入 useI18n()，用 t() 替换文本，并把搜索/过滤/按钮/空态/加载/错误/aria-label/tooltip/确认框等全部切到字典，同时把移动 Basement、删除、Pinned 等 toast 消息改为 i18n。
动态插值与helper：将 formatRelative / formatDate 等传入 lang，让 “X 分钟前 / X min ago” 等文字走 books.* key；search empty state、combined view heading 等需要传参的 t(key, { value }) 统一梳理。
验证：在本地跑 npm run dev，进入书籍页面，切换语言开关，检查所有文本、aria、toast、确认框均正确切换且无 missing-key 警告；必要时补充 smoke test 或截图记录。

执行记录（2025-12-07）
- [x] 梳理 BookMainWidget stack 的所有文本来源，补充 maturity/search/section/卡片上百条文案映射清单。
- [x] 在 `en-US.ts` / `zh-CN.ts` 中落地 `books.*` 命名空间，按 Header、Filters、Sections、Cards、Toasts、Helpers 分组并补上动态插值模板。
- [x] 给 BookMainWidget、Header、FilterBar、SearchBar、BookshelfBooksSection、BookMaturityView 以及 BookFlatCard/RowCard/ShowcaseItem 接入 `useI18n()`，替换 aria/tooltip/toast/确认框/错误副本。
- [x] 让 `bookVisuals.ts` 的 relative time 与 block count helper 接收 `lang` 并缓存 per-locale formatter，Search/Combined 统计 copy 改用 `t(key,{count,keyword})`。
- [x] 本地验证 zh-CN ⇄ en-US 切换后成熟度 summary、search 结果、移动 Basement toast、Pinned badge tooltip 等均随语言更新，无 missing-key 与 console warning。
- [x] 产出 `ADR-163-book-i18n-plan178a.md` 与 VISUAL_RULES 中的 `book_i18n_refresh` 记录，归档决策。

验收/回填
- VISUAL_RULES ✅：已追加 book_i18n_refresh 小节，标注覆盖范围与 helper 要求。
- ADR ✅：ADR-163 描述背景、决策、后果。
- QA ✅：手动切换语言验证 mature view/搜索/空态/toast，暂无自动化需求。