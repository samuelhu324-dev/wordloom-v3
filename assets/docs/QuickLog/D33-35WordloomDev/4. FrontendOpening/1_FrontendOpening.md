frontend/src/
├── lib/
│   ├── config.ts                    ← ✅ 集中配置（API, 主题, 常量）
│   ├── themes.ts                    ← ✅ 可迭代主题系统
│   ├── api/
│   │   ├── client.ts                ← ✅ axios 实例 + 拦截器
│   │   ├── library.ts               ← ✅ /libraries 端点
│   │   └── index.ts
│   └── hooks/
│       ├── useLibraries.ts          ← ✅ TanStack Query wrapper
│       ├── useTheme.ts              ← ✅ 主题切换
│       └── useAuth.ts               ← ✅ 认证状态
├── components/
│   ├── providers/
│   │   ├── AuthProvider.tsx         ← ✅ JWT + 刷新
│   │   ├── ThemeProvider.tsx        ← ✅ CSS Variables 注入
│   │   ├── QueryProvider.tsx        ← ✅ TanStack Query
│   │   └── index.ts
│   ├── ui/
│   │   ├── Button.tsx               ← ✅ 基础按钮
│   │   ├── Input.tsx                ← ✅ 基础输入框
│   │   ├── Modal.tsx                ← ✅ 模态框
│   │   └── Toast.tsx                ← ✅ 提示框
│   ├── library/
│   │   ├── LibraryCard.tsx          ← ✅ 库卡片
│   │   ├── LibrarySelector.tsx      ← ✅ 库选择器
│   │   └── index.ts
│   └── shared/
│       ├── Layout.tsx               ← ✅ 全局布局
│       ├── Header.tsx               ← ✅ 顶部栏
│       └── Sidebar.tsx              ← ✅ 侧边栏
├── styles/
│   ├── tokens.css                   ← ✅ CSS Variables（动态注入）
│   ├── globals.css                  ← ✅ 全局样式
│   └── util-surface.css             ← ✅ 组件基础样式
└── app/
    ├── (auth)/
    │   └── login/
    │       └── page.tsx             ← ✅ 登录页（骨架）
    ├── (admin)/
    │   ├── layout.tsx               ← ✅ 管理后台布局
    │   └── library/
    │       └── page.tsx             ← ✅ 库管理页（垂直切片）
    └── layout.tsx                   ← ✅ 根布局

frontend/docs/
├── FRONTEND_RULES.yaml              ← ✅ 自动生成的前端规则
└── ADR-FR-001.md                    ← ✅ 前端架构决策

frontend/scripts/
└── generate-frontend-rules.py       ← ✅ 规则生成工具