当前后端的问题
WordloomBackend/api/
├─ app/
│  ├─ models/          ← 混合 loom + orbit（不清晰）
│  ├─ routers/         ← 路由层混乱
│  ├─ services/        ← 很少（大量逻辑在模型或路由）
│  └─ core/            ← 工具函数堆积
└─ storage/            ← 物理文件，不应该在代码树里
-----------------------------------------------------
新的后端结构（推荐）
WordloomBackend/
├─ api/
│  ├─ .env.example          # 示例配置
│  ├─ requirements.txt      # 依赖
│  ├─ pyproject.toml        # Poetry 配置（可选但推荐）
│  │
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py           # 应用入口（FastAPI 初始化）
│  │  ├─ config.py         # 配置加载（数据库、API_KEY 等）
│  │  │
│  │  ├─ shared/           # 跨域共享的东西
│  │  │  ├─ __init__.py
│  │  │  ├─ errors.py      # 全局异常类
│  │  │  ├─ schemas.py     # 通用 DTO（Result、PageInfo 等）
│  │  │  ├─ events.py      # 领域事件总线
│  │  │  └─ deps.py        # 依赖注入（数据库会话等）
│  │  │
│  │  ├─ modules/          # ← 核心：按领域划分
│  │  │  ├─ __init__.py
│  │  │  │
│  │  │  ├─ library/       # 领域：图书馆（聚合根 Library）
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ domain.py         # Library、Bookshelf 聚合根 + 值对象
│  │  │  │  ├─ repository.py     # LibraryRepository 接口 + ORM 实现
│  │  │  │  ├─ service.py        # 用例层（CreateLibrary、GetLibrary 等）
│  │  │  │  ├─ router.py         # FastAPI 路由（/library 前缀）
│  │  │  │  ├─ schemas.py        # DTO（LibraryRequest、LibraryResponse）
│  │  │  │  └─ models.py         # SQLAlchemy ORM（内部实现细节）
│  │  │  │
│  │  │  ├─ bookshelf/     # 领域：书架
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /bookshelf
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ book/          # 领域：书籍
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /book
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ block/         # 领域：内容块
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /block
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ chronicle/     # 领域：计时（独立）
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /chronicle
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ stats/         # 领域：统计（独立）
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /stats
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ tag/           # 领域：标签
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /tag
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ theme/         # 领域：主题
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ repository.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /theme
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ models.py
│  │  │  │
│  │  │  ├─ search/        # 技术子域：搜索
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /search
│  │  │  │  └─ schemas.py
│  │  │  │
│  │  │  ├─ media/         # 技术子域：媒体上传
│  │  │  │  ├─ domain.py
│  │  │  │  ├─ service.py
│  │  │  │  ├─ router.py    # /media
│  │  │  │  └─ schemas.py
│  │  │  │
│  │  │  └─ auth/          # 技术子域：认证
│  │  │     ├─ domain.py
│  │  │     ├─ service.py
│  │  │     ├─ router.py
│  │  │     └─ schemas.py
│  │  │
│  │  ├─ infra/            # 基础设施层
│  │  │  ├─ __init__.py
│  │  │  ├─ database.py    # 数据库连接池、会话管理
│  │  │  ├─ storage.py     # 文件存储（S3 或本地）
│  │  │  ├─ cache.py       # Redis 缓存
│  │  │  ├─ event_bus.py   # 事件发布/订阅
│  │  │  └─ logger.py      # 日志配置
│  │  │
│  │  └─ tests/            # 测试（与 app 平行结构）
│  │     ├─ conftest.py
│  │     ├─ test_library/
│  │     ├─ test_bookshelf/
│  │     └─ test_integration/
│  │
│  ├─ migrations/          # 数据库迁移（Alembic）
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions/
│  │
│  └─ storage/             # ← 移到这里或更好地移出项目
│     ├─ orbit_uploads/
│     └─ temp/
│
└─ docs/
   ├─ ARCHITECTURE.md      # 架构文档
   ├─ API.md              # API 文档
   └─ DEVELOPMENT.md      # 开发指南
-----------------------------------------------------
当前前端问题
WordloomFrontend/next/
├─ app/
│  ├─ orbit/
│  │  ├─ page.tsx          ← "use client" 全页面（无 RSC 好处）
│  │  ├─ bookshelves/
│  │  │  └─ page.tsx       ← "use client"
│  │  ├─ tags/
│  │  │  └─ page.tsx       ← "use client"
│  │  ├─ quick-capture/    ← "use client"
│  │  └─ [id]/
│  │     └─ page.tsx       ← "use client"
│  │
│  └─ src/
│     ├─ components/       ← 混合了 Server 和 Client（无标记）
│     ├─ lib/              ← API 调用、工具函数混杂
│     └─ modules/          ← 半吊子的模块化（不清晰）
-----------------------------------------------------
新的前端结构
WordloomFrontend/next/
├─ .env.example
├─ package.json
├─ tsconfig.json
├─ next.config.mjs
│
├─ public/                          # 静态资源
│  └─ uploads/
│
├─ app/                             # ← App Router（Server Components 默认）
│  ├─ layout.tsx                    # ← Server Component（默认）
│  ├─ page.tsx                      # ← Home（Server Component）
│  │
│  ├─ library/
│  │  ├─ layout.tsx                 # ← Server Component
│  │  ├─ page.tsx                   # ← Library 列表页（Server）
│  │  │  # 在这里 fetch 所有 library 数据
│  │  │
│  │  └─ [libraryId]/
│  │     ├─ layout.tsx              # ← Server Component
│  │     └─ page.tsx                # ← Library 详情（Server）
│  │        # 在这里根据 ID 获取 Library 数据
│  │
│  ├─ bookshelf/
│  │  ├─ [bookshelfId]/
│  │  │  ├─ layout.tsx              # ← Server Component
│  │  │  └─ page.tsx                # ← Bookshelf 详情（Server）
│  │  │     # fetch 书架 + 书籍列表
│  │  │     # 返回 <BookshelfClient initialData={data} />
│  │  │
│  │  └─ components/
│  │     └─ BookshelfClient.tsx      # ← "use client"（仅交互部分）
│  │
│  ├─ book/
│  │  ├─ [bookId]/
│  │  │  ├─ layout.tsx              # ← Server Component
│  │  │  └─ page.tsx                # ← Book 编辑页（Server）
│  │  │     # fetch book + blocks
│  │  │     # 返回 <BookPageClient initialBook={data} />
│  │  │
│  │  └─ components/
│  │     ├─ BookPageClient.tsx       # ← "use client"（编辑交互）
│  │     └─ BlockRenderer.tsx        # ← "use client"（Block 渲染）
│  │
│  ├─ chronicle/
│  │  ├─ layout.tsx                 # ← Server Component
│  │  ├─ page.tsx                   # ← Chronicle 仪表盘（Server）
│  │  │  # fetch 所有计时数据 + 统计
│  │  │  # 返回 <ChronicleClient initialStats={data} />
│  │  │
│  │  ├─ sessions/
│  │  │  └─ [sessionId]/
│  │  │     └─ page.tsx             # ← Session 详情（Server）
│  │  │
│  │  └─ components/
│  │     ├─ ChronicleClient.tsx      # ← "use client"（控制面板）
│  │     └─ TimingWidget.tsx         # ← "use client"（计时器）
│  │
│  ├─ stats/
│  │  ├─ layout.tsx                 # ← Server Component
│  │  ├─ page.tsx                   # ← Stats 仪表盘（Server）
│  │  │  # fetch 所有统计数据（聚合）
│  │  │  # 返回 <StatsClient initialData={data} />
│  │  │
│  │  └─ components/
│  │     ├─ StatsClient.tsx          # ← "use client"（图表交互）
│  │     └─ ChartModule.tsx          # ← "use client"
│  │
│  ├─ theme/
│  │  ├─ layout.tsx
│  │  ├─ page.tsx                   # ← 主题编辑器（Server + Client 混合）
│  │  │  # 获取当前主题配置
│  │  │  # 返回 <ThemeEditorClient initialTheme={data} />
│  │  │
│  │  ├─ presets/
│  │  │  └─ page.tsx                # ← 主题预设库（Server）
│  │  │
│  │  └─ components/
│  │     └─ ThemeEditorClient.tsx    # ← "use client"（编辑交互）
│  │
│  ├─ search/
│  │  ├─ layout.tsx
│  │  ├─ page.tsx                   # ← 搜索结果（Server）
│  │  │  # 根据 query 参数搜索
│  │  │  # 返回 <SearchClient results={data} />
│  │  │
│  │  └─ components/
│  │     └─ SearchClient.tsx        # ← "use client"（搜索表单）
│  │
│  └─ preferences/
│     ├─ layout.tsx
│     ├─ page.tsx                   # ← 设置页（Server）
│     └─ components/
│        └─ PreferencesClient.tsx    # ← "use client"
│
├─ src/
│  ├─ components/
│  │  ├─ ui/                         # 通用 UI 组件（都应该标 "use client"）
│  │  │  ├─ Button.tsx
│  │  │  ├─ Modal.tsx
│  │  │  ├─ Sidebar.tsx
│  │  │  └─ ThemeSwitcher.tsx
│  │  │
│  │  ├─ blocks/                     # Block 渲染器（Client Component）
│  │  │  ├─ CheckPointBlockView.tsx  # ← "use client"
│  │  │  ├─ TextBlockView.tsx        # ← "use client"
│  │  │  ├─ CodeBlockView.tsx        # ← "use client"
│  │  │  └─ BlockFactory.tsx         # ← "use client"
│  │  │
│  │  └─ shared/
│  │     ├─ AppLayout.tsx            # ← "use client"（菜单、导航）
│  │     └─ ErrorBoundary.tsx        # ← "use client"
│  │
│  ├─ lib/
│  │  ├─ api/                        # API 客户端（Server Action 支持）
│  │  │  ├─ client.ts               # 原始 fetch 封装
│  │  │  ├─ library.ts              # Library API
│  │  │  ├─ bookshelf.ts            # Bookshelf API
│  │  │  ├─ book.ts                 # Book API
│  │  │  ├─ chronicle.ts            # Chronicle API
│  │  │  ├─ stats.ts                # Stats API
│  │  │  └─ theme.ts                # Theme API
│  │  │
│  │  ├─ utils/
│  │  │  ├─ format.ts               # 格式化函数
│  │  │  ├─ image.ts                # 图片工具
│  │  │  └─ validators.ts           # 验证函数
│  │  │
│  │  ├─ types/
│  │  │  ├─ index.ts                # 全局类型
│  │  │  ├─ api.ts                  # API 响应类型
│  │  │  ├─ domain.ts               # 领域模型类型
│  │  │  └─ ui.ts                   # UI 状态类型
│  │  │
│  │  └─ hooks/
│  │     ├─ useBook.ts              # ← "use client" hook
│  │     ├─ useChronicle.ts         # ← "use client" hook
│  │     └─ useTheme.ts             # ← "use client" hook
│  │
│  ├─ modules/
│  │  ├─ chronicle/
│  │  │  ├─ domain.ts               # 计时的核心概念（纯数据）
│  │  │  ├─ services.ts             # 业务逻辑（可以在 Server/Client 用）
│  │  │  ├─ queries.ts              # React Query 查询定义
│  │  │  └─ ui/
│  │  │     ├─ ChronicleWidget.tsx   # ← "use client"
│  │  │     └─ TimingControl.tsx     # ← "use client"
│  │  │
│  │  ├─ stats/
│  │  │  ├─ domain.ts
│  │  │  ├─ services.ts
│  │  │  ├─ queries.ts
│  │  │  └─ ui/
│  │  │     ├─ StatsPanel.tsx        # ← "use client"
│  │  │     └─ Charts.tsx            # ← "use client"
│  │  │
│  │  ├─ theme/
│  │  │  ├─ domain.ts
│  │  │  ├─ presets.ts              # 主题预设
│  │  │  ├─ services.ts
│  │  │  └─ ui/
│  │  │     ├─ ThemeEditor.tsx       # ← "use client"
│  │  │     └─ PresetGallery.tsx     # ← "use client"
│  │  │
│  │  └─ search/
│  │     ├─ domain.ts
│  │     ├─ services.ts
│  │     └─ ui/
│  │        ├─ SearchBar.tsx         # ← "use client"
│  │        └─ ResultsList.tsx       # ← "use client"
│  │
│  ├─ providers/
│  │  ├─ QueryProvider.tsx           # ← "use client"
│  │  ├─ ThemeProvider.tsx           # ← "use client"
│  │  └─ UserProvider.tsx            # ← "use client"
│  │
│  └─ styles/
│     ├─ globals.css
│     ├─ variables.css               # CSS 变量（主题）
│     └─ components.css
│
└─ tests/
   ├─ unit/
   │  ├─ lib/
   │  └─ components/
   │
   └─ e2e/
      └─ main.spec.ts
