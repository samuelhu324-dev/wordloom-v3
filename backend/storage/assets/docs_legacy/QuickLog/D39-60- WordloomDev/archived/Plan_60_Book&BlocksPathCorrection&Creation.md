Plan: Book 资产页与 Block 工作台梳理
完成 /admin/books/[bookId]→“Book 资产页”、/admin/blocks→“块工作台” 的分工，并补齐 Book 页指标数据，让用户在书架→Book→Block 的路径上获取完整信息。

Steps
整理导航链路：Library 列表→Bookshelf 列表→Book 资产页→Block 工作台，确认 router.push 与面包屑文案在相关页面更新（admin/libraries、admin/bookshelves/[bookshelfId]、admin/books/[bookId]、admin/blocks）。
补充 Book 资产页数据源：在 page.tsx 汇总 Blocks 数、Stable Blocks、覆盖率、Chronicle 事件数、本周查看等字段（先用 hook 统计，缺失数据标记 TODO）。
调整 Block 工作台（page.tsx）确保默认从 book_id query 读取，并在 Book 页 CTA、书架页入口提供跳转；同时保持原 Tabs + Inline 编辑体验。
优化组件拆分：将 Book 资产页的 Hero/指标/InfoPanel 拆成 book 下复用组件（如 BookHeroCard, BookInfoPanel），Block 工作台复用既有 BlockList 等组件。
更新规则文档：同步修改 VISUAL_RULES.yaml、HEXAGONAL_RULES.yaml、DDD_RULES.yaml，记录 Book/Block 路由职责和成熟度展示范围的调整。
Further Considerations
Book 页指标缺口：是否需要后端新增 Stable Blocks / view-count API？若暂缺，准备占位字段或注释。
Bookshelf 点击后默认进入 Book 资产页还是直接进入 Block 工作台？B 直接工作台
