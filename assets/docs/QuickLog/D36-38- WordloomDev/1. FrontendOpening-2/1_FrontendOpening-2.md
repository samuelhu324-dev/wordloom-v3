Plan: 从零开始 - 基于行业最佳实践的FSD前端重建
你需要的不是迁移而是完全重建。Wordloom 的 UI 是 unified page 多域模型（Library → Bookshelf → Book → Block，同时 Tag/Media/Search 可在同页面访问），这更接近 Notion/Linear/Figma 的架构，而不是简单的 CRUD 系统。

核心认识
你现在的"僵局"根源：

45 个组件分散 10 个文件夹，没有清晰的公开 API 边界
Tag/Media/Search 只有 UI，缺 hooks/API（特性不完整）
ADR-057 设计了"4层垂直切片"，但没有被严格执行成 FSD
404 + 编码错误是旧代码的遗留物，不值得修复
为什么要从零开始：

✅ 旧代码已经有 ADR-057 + ADR-059 的设计文档
✅ 后端 API 已完全就绪（73个端点）
❌ 前端实现与文档不对齐（预设计 > 实际代码）
最优决策：用 ADR-057 的架构从零重建，而不是修补旧代码
Wordloom 的真实需求：

单页应用（SPA/类 SPA）：用户在一个主页面中切换 Library → Bookshelf → Book → Block
四层导航嵌套：与后端领域模型 1:1 对应
六个独立通道（features）：Library + Bookshelf + Book + Block + Tag/Media (并行) + Search (异步)
强类型整合：TanStack Query + TypeScript 严格模式
行业参考范本分析

1. Notion / Linear 模式（✅ 最匹配 Wordloom）
结构：Workspace → Database → Records → Fields
对应：Library  → Bookshelf → Books   → Blocks

特点：
- 层级嵌套显示（Sidebar 始终展示全路径）
- 实时同步状态（WebSocket 可选，现阶段不需）
- 富编辑器（Block 级别的编辑器，Wordloom 需要）

为什么匹配？ Notion 的聚合根设计（Workspace = Library，Database = Bookshelf）与 Wordloom DDD 一致。

2. SkyPro / Tinkoff FSD 标准（✅ 组织最清晰）
slices/
  ├── entities/          # 领域模型（Library、Book、Block DTOs）
  ├── features/          # 业务特性（CRUD操作）
  ├── widgets/           # 合成组件（多个 features 组合）
  ├── pages/             # 路由层
  └── shared/            # 共享（UI、工具、类型）

关键特性：

严格的单向依赖（entities < features < widgets < pages）
特性内部：model（API+hooks）+ ui（components）
每个特性暴露 index.ts 作为公开 API

3. Figma 处理 Frames → Groups → Shapes 的深层嵌套结构：

每层都有对应的 hook（useSelectedFrame, useSelectedGroup）
状态管理：Zustand 管理当前选中上下文
性能：虚拟滚动 + 懒加载组件

推荐的 Wordloom FSD 结构（生产级）
src/
├── shared/                                    [Layer 0] Infrastructure
│   ├── api/
│   │   ├── client.ts                 ✅ Axios instance + JWT interceptor
│   │   ├── types.ts                  ✅ BaseDto + Error types
│   │   └── index.ts                  ✅ barrel export
│   ├── ui/
│   │   ├── Button.tsx                ✅ Primary action button
│   │   ├── Card.tsx                  ✅ Content container
│   │   ├── Input.tsx                 ✅ Text input field
│   │   ├── Modal.tsx                 ✅ Dialog component
│   │   ├── Spinner.tsx               ✅ Loading spinner
│   │   ├── Toast.tsx                 ⚠️ MISSING
│   │   ├── Skeleton.tsx              ⚠️ MISSING
│   │   └── index.ts                  ✅ barrel export
│   ├── layouts/
│   │   ├── Layout.tsx                ✅ Main page wrapper (Header+Sidebar+Content)
│   │   ├── Header.tsx                ✅ Top navigation bar
│   │   ├── Sidebar.tsx               ✅ Left menu navigation
│   │   └── index.ts                  ✅ barrel export
│   ├── providers/
│   │   ├── ThemeProvider.tsx         ✅ CSS variable injection
│   │   ├── AuthProvider.tsx          ⚠️ MISSING (planned)
│   │   └── index.ts                  ✅ barrel export
│   ├── lib/
│   │   ├── config.ts                 ✅ Environment config
│   │   ├── utils.ts                  ✅ Utility functions
│   │   ├── validators.ts             ⚠️ MISSING
│   │   ├── errors.ts                 ⚠️ MISSING (error mapping)
│   │   └── index.ts                  ✅ barrel export
│   └── styles/
│       ├── tokens.css                ✅ Design system variables
│       ├── globals.css               ✅ Global resets
│       └── *.module.css              ✅ Component-scoped styles
│
├── entities/                                  [Layer 1] Domain Models (100% complete)
│   ├── library/{types.ts, index.ts}  ✅ LibraryDto
│   ├── bookshelf/{types.ts, index.ts} ✅ BookshelfDto
│   ├── book/{types.ts, index.ts}     ✅ BookDto
│   ├── block/{types.ts, index.ts}    ✅ BlockDto (6 types)
│   ├── tag/{types.ts, index.ts}      ✅ TagDto
│   ├── media/{types.ts, index.ts}    ✅ MediaDto
│   └── search/{types.ts, index.ts}   ✅ SearchDto
│
├── features/                                  [Layer 2] Business Logic
│   ├── library/
│   │   ├── model/
│   │   │   ├── api.ts                ✅ 5 functions (list/get/create/update/delete)
│   │   │   └── hooks.ts              ✅ 5 hooks (useLibraries, etc.)
│   │   ├── ui/
│   │   │   ├── LibraryCard.tsx       ✅ Card display
│   │   │   ├── LibraryList.tsx       ✅ List container
│   │   │   └── index.ts              ✅ barrel export
│   │   └── index.ts                  ✅ Feature public API
│   ├── bookshelf/                     ✅ Same pattern as library
│   ├── book/                          ✅ Same pattern as library
│   ├── block/
│   │   ├── model/{api.ts, hooks.ts}  ✅ Complete
│   │   ├── ui/
│   │   │   ├── BlockCard.tsx         ✅ Single block display
│   │   │   ├── BlockList.tsx         ✅ Block list container
│   │   │   ├── BlockEditor.tsx       ❌ MISSING (rich editor)
│   │   │   └── index.ts              ✅ barrel export
│   │   └── index.ts                  ✅ Feature public API
│   ├── tag/
│   │   ├── model/{api.ts, hooks.ts}  ✅ Complete
│   │   ├── ui/
│   │   │   ├── TagBadge.tsx          ✅ Tag display
│   │   │   ├── TagList.tsx           ✅ Tag list
│   │   │   ├── TagSelector.tsx       ❌ MISSING (picker)
│   │   │   ├── TagManager.tsx        ❌ MISSING (management UI)
│   │   │   └── index.ts              ✅ barrel export
│   │   └── index.ts                  ✅ Feature public API
│   ├── media/
│   │   ├── model/{api.ts, hooks.ts}  ✅ Complete
│   │   ├── ui/
│   │   │   ├── MediaCard.tsx         ✅ Media thumbnail
│   │   │   ├── MediaList.tsx         ✅ Media grid
│   │   │   ├── MediaUploader.tsx     ❌ MISSING (file upload)
│   │   │   ├── MediaGallery.tsx      ❌ MISSING (gallery view)
│   │   │   ├── MediaViewer.tsx       ❌ MISSING (full view)
│   │   │   └── index.ts              ✅ barrel export
│   │   └── index.ts                  ✅ Feature public API
│   └── search/
│       ├── model/{api.ts, hooks.ts}  ✅ Complete
│       ├── ui/
│       │   ├── SearchBar.tsx         ❌ MISSING (input)
│       │   ├── SearchResults.tsx     ✅ Results display
│       │   ├── SearchFilters.tsx     ❌ MISSING (filter panel)
│       │   └── index.ts              ✅ barrel export
│       └── index.ts                  ✅ Feature public API
│
├── widgets/                                   [Layer 3] Composed Features
│   ├── library/{LibraryMainWidget.tsx, index.ts} ✅
│   ├── bookshelf/{BookshelfMainWidget.tsx, index.ts} ✅
│   ├── book/{BookMainWidget.tsx, index.ts}  ✅
│   ├── block/{BlockMainWidget.tsx, index.ts} ✅ (incomplete without editor)
│   ├── sidebar-nav/{SidebarNav.tsx, index.ts} ❌ MISSING (breadcrumbs + nav)
│   └── search-panel/{SearchPanel.tsx, index.ts} ❌ MISSING (composed search)
│
├── app/                                       [Layer 6] Root Layout & Providers
│   ├── layout.tsx                   ✅ Root <html> + Providers
│   ├── providers.tsx                ✅ ThemeProvider + QueryProvider
│   ├── page.tsx                     ✅ Welcome page
│   ├── (auth)/
│   │   └── login/page.tsx           ✅ Login form
│   └── (admin)/
│       ├── layout.tsx               ✅ Admin Layout wrapper
│       ├── dashboard/page.tsx       ✅ Dashboard (50% complete)
│       ├── libraries/page.tsx       ✅ Libraries CRUD (100% complete)
│       ├── bookshelves/page.tsx     ⚠️ List only (50%)
│       ├── books/page.tsx           ⚠️ List only (50%)
│       ├── tags/page.tsx            ❌ Placeholder (10%)
│       ├── media/page.tsx           ❌ Placeholder (10%)
│       └── search/page.tsx          ❌ Placeholder (10%)
│
└── MISSING DYNAMIC ROUTES:
    ├── (admin)/libraries/[libraryId]/page.tsx  ❌
    ├── (admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/page.tsx ❌
    ├── (admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]/page.tsx ❌
```

建立共享基础层（Week 1 前2天）：创建 shared/目录，包含 API 客户端、UI 组件库、全局样式、类型定义、工具函数，确保零 404、正确的 TypeScript 类型。

定义领域实体层（Week 1 后2天）：在 entities/ 中为 7 个领域各建 types.ts（只有类型，零业务逻辑），与后端 DDD 模型 1:1 对应，启用 TypeScript 严格模式。

实现特性的模型层（Week 2 前3天）：按优先级 (Library → Bookshelf → Book → Block → Tag → Media → Search)，为每个特性创建 features/xxx/model/{api.ts, hooks.ts, store.ts}，全部连接真实后端 API。

实现特性的 UI 层（Week 2 后4天）：为每个特性创建 features/xxx/ui/ 组件，集成 hooks，建立一致的组件 API（Card/List/Form/Detail 模式），每个特性暴露 index.ts 公开 API。

构建版面层和路由（Week 3）：创建 widgets/ 合成多特性的版面，创建 pages/ 的嵌套路由，实现 Library → Bookshelf → Book → Block 的四层导航，测试端到端流程。

文档和质量把关（Week 3 末）：补充 ADR（FSD 决策记录）、类型契约文档、组件公开 API 文档，配置 Vitest + 初始测试框架，检查循环依赖。

Further Considerations
现有 45 个旧组件怎么处理？ 全部废弃。从零开始的代价 < 修复旧代码的代价（旧代码已经有 404 + 编码问题，不值得投入）。参考代码可以保留用于学习。

Zustand store 是否必须？ 对于四层嵌套（当前选中的 Library/Bookshelf/Book）推荐使用，简化 Props Drilling。不过初期可以用 URL params + TanStack Query 代替，逐步优化。

TypeScript 严格模式和 ESLint 检查？ 从一开始就启用，后续调整难度大。设置 strict mode，配置 madge 检测循环依赖。

性能考量（Block 编辑器可能很重）？

虚拟滚动（Block 列表很长时）
React.memo 分解编辑器
代码分割：BlockEditor 懒加载
何时开始测试？ 不急。先完成 Week 2-3 的主体功能，再回头加测试。但从一开始就设计可测性（model/ui 分离、纯组件）。

行业成熟范本参考
Template 1: Tinkoff 开源 FSD 参考 ⭐ 强烈推荐
链接：https://github.com/feature-sliced/examples (官方例子)
为什么：最严格的 FSD 实现，多 TypeScript 强制约束
参考点：
如何使用 barrel exports (index.ts) 建立公开 API
特性内部的 model/ui 严格分离
shared/ 和 entities/ 的边界定义

Template 2: Notion 公开技术讨论 ⭐ 学习嵌套导航
资源：Notion Tech Talks YouTube + 工程博客
参考点：
处理 Workspace → Database → Records 嵌套
面包屑导航 + 侧边栏状态同步
大规模前端的权限管理（暂时不需，但架构要支持）

Template 3: Linear 开源代码库研究 ⭐ 实战参考
链接：https://github.com/linear (部分开源)
参考点：
4 层嵌套（Team → Project → Issue → Comments）
实时协作基础（可选，Wordloom v2 功能）
性能优化（虚拟滚动 + 懒加载）
现在我已经给你完整的分析和方案。你认真看一下，有任何疑问或调整需求，我们再深入讨论具体实现的细节。