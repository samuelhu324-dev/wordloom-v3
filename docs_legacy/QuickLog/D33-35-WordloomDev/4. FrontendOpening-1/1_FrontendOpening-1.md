frontend/src/
├── lib/
│   ├── config.ts                    ✅ 全局配置
│   ├── themes.ts                    ✅ 主题系统
│   ├── api/
│   │   ├── client.ts                ✅ Axios 实例
│   │   ├── types.ts                 ✅ TypeScript 接口（Library, Bookshelf, Book, Block）
│   │   ├── library.ts               ✅ Library API
│   │   ├── bookshelf.ts             ✅ Bookshelf API（新）
│   │   ├── book.ts                  ✅ Book API（新）
│   │   ├── block.ts                 ✅ Block API（新）
│   │   └── index.ts                 ✅ 统一导出
│   └── hooks/
│       ├── useLibraries.ts          ✅ Library 查询
│       ├── useBookshelves.ts        ✅ Bookshelf 查询（新）
│       ├── useBooks.ts              ✅ Book 查询（新）
│       ├── useBlocks.ts             ✅ Block 查询（新）
│       ├── useTheme.ts              ✅ 主题切换
│       ├── useAuth.ts               ✅ 认证
│       └── useToast.ts              ✅ 提示
│
├── components/
│   ├── ui/
│   │   ├── Button.tsx               ✅ 基础按钮（无业务）
│   │   ├── Input.tsx                ✅ 基础输入（无业务）
│   │   ├── Modal.tsx                ✅ 模态框（无业务）
│   │   ├── Card.tsx                 ✅ 卡片（无业务）
│   │   ├── Badge.tsx                ✅ 标签（无业务）
│   │   ├── Spinner.tsx              ✅ 加载态（无业务）
│   │   ├── Toast.tsx                ✅ 提示（无业务）
│   │   └── index.ts
│   │
│   ├── library/
│   │   ├── LibraryCard.tsx          ✅ 库卡片
│   │   ├── LibraryList.tsx          ✅ 库列表
│   │   ├── LibraryForm.tsx          ✅ 库表单（新建/编辑）
│   │   ├── DeleteLibraryModal.tsx   ✅ 删除确认（新）
│   │   └── index.ts
│   │
│   ├── bookshelf/                   ✅ 新增（原来缺失）
│   │   ├── BookshelfCard.tsx
│   │   ├── BookshelfList.tsx
│   │   ├── BookshelfForm.tsx
│   │   └── index.ts
│   │
│   ├── book/                        ✅ 新增（原来缺失）
│   │   ├── BookCard.tsx
│   │   ├── BookList.tsx
│   │   ├── BookForm.tsx
│   │   └── index.ts
│   │
│   ├── block/                       ✅ 新增（原来缺失）
│   │   ├── BlockEditor.tsx
│   │   ├── BlockList.tsx
│   │   ├── BlockDragHandle.tsx
│   │   └── index.ts
│   │
│   ├── providers/
│   │   ├── AuthProvider.tsx         ✅ JWT + 刷新
│   │   ├── ThemeProvider.tsx        ✅ CSS Variables 注入
│   │   ├── QueryProvider.tsx        ✅ TanStack Query
│   │   └── index.ts
│   │
│   └── shared/
│       ├── Layout.tsx               ✅ 页面外框
│       ├── Header.tsx               ✅ 顶部栏
│       ├── Sidebar.tsx              ✅ 侧边栏
│       ├── BreadCrumb.tsx           ✅ 面包屑
│       └── index.ts
│
├── styles/
│   ├── tokens.css                   ✅ CSS Variables
│   ├── globals.css                  ✅ 全局样式
│   └── util-surface.css             ✅ 工具类
│
└── app/
    ├── (auth)/
    │   └── login/
    │       └── page.tsx             ✅ 登录页
    │
    ├── (admin)/
    │   ├── layout.tsx               ✅ 后台布局（Header + Sidebar）
    │   ├── dashboard/
    │   │   └── page.tsx             ✅ 库列表（首页）
    │   ├── libraries/[id]/
    │   │   └── page.tsx             ✅ 库详情 → 书架列表
    │   ├── bookshelves/[id]/
    │   │   └── page.tsx             ✅ 书架详情 → 书籍列表（新）
    │   ├── books/[id]/
    │   │   ├── page.tsx             ✅ 书籍详情 → 块列表（新）
    │   │   └── edit/
    │   │       └── page.tsx         ✅ 块编辑页面（新）
    │   └── tags/
    │       └── page.tsx             ✅ 标签管理（全局）
    │
    └── layout.tsx                   ✅ 根布局