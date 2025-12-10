📋 三个页面的 UI 完整实现方案
🎯 设计目标
Library 界面: Bookshelf 卡片预览（有插图 + 标题 + 说明）
Bookshelf 界面: Book 小卡片列表（title + description + cover 图）
Book 界面: 通用文本块编辑器（仅支持纯文本 + 基础格式）

方案 A: UI 组件架构
第1层：Shared Base Components ✅ 已有

shared/ui/
├── Button.tsx (primary, secondary, danger, ghost)
├── Card.tsx (with overlay + hover)
├── Input.tsx (text input with validation)
├── Modal.tsx (dialog wrapper)
├── Spinner.tsx (loading indicator)
├── Toast.tsx ⬅️ 需创建 (通知组件)
└── Breadcrumb.tsx ⬅️ 需创建 (导航面包屑)

第2层：Domain-Specific Cards 需部分增强
features/
├── library/ui/
│   ├── LibraryCard.tsx ✅
│   ├── LibraryList.tsx ✅
│   └── BookshelfPreviewCard.tsx ⬅️ 需创建 (含插图)
│
├── bookshelf/ui/
│   ├── BookshelfCard.tsx ✅
│   ├── BookshelfList.tsx ✅
│   ├── BookPreviewCard.tsx ⬅️ 需创建 (含cover)
│   └── BookshelfHeader.tsx ✅
│
├── book/ui/
│   ├── BookCard.tsx ✅
│   ├── BookList.tsx ✅
│   └── BlockList.tsx ⬅️ 需创建 (块列表)
│
└── block/ui/
    ├── BlockCard.tsx ✅
    ├── BlockEditor.tsx ⬅️ 🔴 CRITICAL (Slate.js)
    └── BlockViewer.tsx ⬅️ 需创建 (只读模式)

第3层：Page Layouts 需更新
app/(admin)/
├── libraries/
│   ├── page.tsx ✅ (列表)
│   └── [libraryId]/page.tsx (需增强: BookshelfPreviewGrid)
│
├── bookshelves/
│   ├── page.tsx ✅ (列表)
│   └── [bookshelfId]/page.tsx (需增强: BookGrid)
│
└── books/
    ├── page.tsx ✅ (列表)
    └── [bookId]/page.tsx (需增强: BlockEditor集成)


方案 B: 三个页面的具体布局
页面 1: Library 详情页
/admin/libraries/[libraryId]

┌─────────────────────────────────────┐
│ 📖 我的书库 (Title)                   │
│ 这是一个测试... (Description)        │
├─────────────────────────────────────┤
│ [新建书橱] 按钮                       │
├─────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  │ [插图占位图]    │ │ [插图占位图]    │ │ [插图占位图]    │
│  │                │ │                │ │                │
│  │ 阅读中          │ │ 已读           │ │ 待读            │
│  │ 正在阅读的书... │ │ 已经读过的... │ │ 想要读的...    │
│  │ 5 本书 📚      │ │ 12 本书 📚    │ │ 8 本书 📚     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘
│
└─────────────────────────────────────┘

组件: BookshelfPreviewCard (新)
  - cover image (placeholder or from first book)
  - bookshelf.name
  - bookshelf.description
  - book count badge
  - click → navigate to /admin/bookshelves/[id]

页面 2: Bookshelf 详情页
/admin/bookshelves/[bookshelfId]

┌─────────────────────────────────────┐
│ 📚 阅读中 (Bookshelf Name)           │
│ 正在阅读的书籍... (description)     │
├─────────────────────────────────────┤
│ [新建书籍] 按钮                      │
├─────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐
│  │ [Cover]  │ │ [Cover]  │ │ [Cover]  │
│  │ Python基础 │ │ JavaScript│ │ TypeScript│
│  │ 作者名   │ │ 作者名   │ │ 作者名   │
│  │ 进度: 50% │ │ 进度: 0% │ │ 进度: 100%│
│  └──────────┘ └──────────┘ └──────────┘
│
│  ┌──────────┐ ┌──────────┐ ...
│  │ [Cover]  │ │ [Cover]  │
│  │ React开发 │ │ Vue 3     │
│  ...
└─────────────────────────────────────┘

组件: BookPreviewCard (新)
  - cover image (book.cover_media_id or placeholder)
  - book.name
  - book description (truncated)
  - progress bar (可选)
  - click → navigate to /admin/books/[id]

页面 3: Book 详情页 + BlockEditor
/admin/books/[bookId]

┌─────────────────────────────────────┐
│ ← 返回 | 📖 Python基础 | [保存] [删除]│
├─────────────────────────────────────┤
│ 第1章: 基础语法                      │
│ 作者: XXX | 创建: 2025-11-10        │
├─────────────────────────────────────┤
│ [+ 新增文本块] 按钮                  │
├─────────────────────────────────────┤
│ ┌──────────────────────────────────┐│
│ │ Block #1 - 文本块                 ││
│ │ ┌──────────────────────────────┐ ││
│ │ │ 第一章介绍了...               │ ││
│ │ │ ... (可编辑富文本)            │ ││
│ │ └──────────────────────────────┘ ││
│ │ [编辑] [删除] 创建: 2025-11-01   ││
│ └──────────────────────────────────┘│
│                                     │
│ ┌──────────────────────────────────┐│
│ │ Block #2 - 文本块                 ││
│ │ ┌──────────────────────────────┐ ││
│ │ │ 第二章讲解了...               │ ││
│ │ │ ... (可编辑富文本)            │ ││
│ │ └──────────────────────────────┘ ││
│ │ [编辑] [删除] 创建: 2025-11-02   ││
│ └──────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘

组件: BlockEditor (新 - 🔴 CRITICAL)
  - rich text input (Slate.js recommended)
  - toolbar: Bold, Italic, Code, Link, List, etc.
  - inline editing or modal mode
  - auto-save to backend

组件: BlockList (新)
  - grid/list of BlockCard items
  - drag-to-reorder support (Phase 6)
  - inline block editor (Phase 5)


方案 C: CSS 样式系统 + 响应式设计
CSS 变量完整方案
/* tokens.css 增强 */

:root {
  /* Colors - Extended for card designs */
  --color-card-bg: #ffffff;
  --color-card-hover: #f8f9fa;
  --color-card-border: #e0e0e0;
  --color-overlay-dark: rgba(0, 0, 0, 0.7);

  /* Card-specific */
  --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --card-shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.15);
  --card-radius: 12px;

  /* Spacing for grids */
  --grid-gap: var(--spacing-lg);
  --grid-cols-mobile: 1;
  --grid-cols-tablet: 2;
  --grid-cols-desktop: 3;

  /* Typography for card text */
  --card-title-size: 16px;
  --card-desc-size: 14px;
  --card-badge-size: 12px;
}

[data-theme="dark"] {
  --color-card-bg: #1e1e1e;
  --color-card-hover: #2a2a2a;
  --color-card-border: #333333;
}

[data-theme="loom"] {
  /* 灰蓝主题 */
  --color-primary: #4a90b8;
  --color-card-bg: #f0f4f8;
  --color-card-hover: #e8eef7;
  --color-card-border: #b8c5d6;
}

/* 响应式 */
@media (max-width: 768px) {
  :root {
    --grid-cols: 2;
    --grid-gap: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  :root {
    --grid-cols: 1;
  }
}

卡片组件样式模板
// BookshelfPreviewCard.module.css
.card {
  display: flex;
  flex-direction: column;
  background: var(--color-card-bg);
  border: 1px solid var(--color-card-border);
  border-radius: var(--card-radius);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--card-shadow);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--card-shadow-hover);
  border-color: var(--color-primary);
}

.cover {
  position: relative;
  width: 100%;
  aspect-ratio: 3 / 4; /* 图书常见宽高比 */
  background: linear-gradient(135deg, var(--color-bg-secondary), var(--color-bg-tertiary));
  overflow: hidden;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  inset: 0;
  background: var(--color-overlay-dark);
  opacity: 0;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card:hover .overlay {
  opacity: 1;
}

.content {
  padding: var(--spacing-md);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.title {
  font-size: var(--card-title-size);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs) 0;
  line-clamp: 2; /* 截断2行 */
}

.description {
  font-size: var(--card-desc-size);
  color: var(--color-text-secondary);
  margin: 0 0 auto 0;
  line-clamp: 2; /* 截断2行 */
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--card-badge-size);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  padding: 4px 8px;
  border-radius: 12px;
  margin-top: var(--spacing-sm);
  width: fit-content;
}

方案 D: 规则文件同步方案
需更新的部分
文件	部分	当前状态	修改内容
VISUAL_RULES.yaml	Part 13-15	未实现	补充卡片设计系统（cover ratio, overlay, hover effect）
VISUAL_RULES.yaml	Part 1: Theme	Loom 主题缺失	添加 Loom 主题的完整变量定义
DDD_RULES.yaml	domain_to_ui_mapping	空白	添加每个 Domain 对应的 UI Component Props
HEXAGONAL_RULES.yaml	ui_integration_guidelines	模糊	明确 Independent Aggregates 如何在 UI 中表现
所有 *.module.css	所有文件	可能硬编码颜色	替换为 CSS 变量 var(--color-*)

✨ 成熟可靠的行业建议
1️⃣ 架构建议
✅ 采用 Atomic Design + FSD 混合

Atoms: Button, Input, Spinner (✅ 已有)
Molecules: Card, Input+Label, Button Group (✅ 已有)
Organisms: BookshelfPreviewCard, BlockEditor (🟡 需创建)
Templates: Page layouts (✅ 已有)
Pages: Route-level components (✅ 已有)

2️⃣ 样式系统建议
✅ CSS 变量 + Tailwind 混合 (当前用纯CSS变量 ✅)

优势: 轻量级 + 主题切换无需重编译
劣势: 缺乏响应式工具类
建议：保持现有 CSS 变量系统，但添加如下增强：

/* 响应式工具类 */
.grid-responsive {
  display: grid;
  grid-template-columns: repeat(var(--grid-cols), 1fr);
  gap: var(--grid-gap);
}

@media (max-width: 768px) {
  :root { --grid-cols: 2; }
}

3️⃣ BlockEditor 选型建议 🔴 CRITICAL
当前三个选择（行业标准）：

框架	优点	缺点	推荐度
Slate.js	高定制性，插件架构，React原生	学习曲线陡，绑定React	⭐⭐⭐⭐⭐
ProseMirror	稳定成熟，支持协作编辑	非React，学习难度高	⭐⭐⭐⭐
Draft.js	Facebook维护，相对简单	维护中止，功能受限	⭐⭐
Tiptap	Slate+ProseMirror融合，简单API	商业版本，小众	⭐⭐⭐⭐

推荐: Slate.js (满足 Wordloom 需求)

✅ React 原生集成
✅ 轻量级但可高度定制
✅ 完善的插件生态
✅ 支持 Collaborative editing (未来需求)
POC 实现周期: 2-3 天


4️⃣ 图片处理建议
当前 cover image 存储方案：

Phase A (现在): Placeholder + localStorage （建议先用这个快速验证）
Phase B (下周): Media 关联 + S3 upload （完整方案）
// BookshelfPreviewCard 中的图片处理
const getCoverImage = (coverMediaId?: string) => {
  if (coverMediaId) {
    return `/api/v1/media/${coverMediaId}`;
  }
  // Phase A: localStorage placeholder
  return localStorage.getItem(`bookshelf-cover-${id}`) || '/placeholder-book.svg';
};


5️⃣ 响应式设计建议
基于 Wordloom 的学习/笔记场景，建议的断点：
Mobile (< 640px):  1 column cards
Tablet (640-1024): 2 column cards
Desktop (> 1024):  3 column cards


Card 最小宽度: 280px (保证可读性)
Card 最大宽度: 400px (保证不过宽)
触摸目标: 最小 44×44px (A11y 标准)

6️⃣ 状态管理建议
当前使用 TanStack Query ✅

建议的状态分层：
URL State (Next.js Router) ← 路由参数: libraryId, bookshelfId
  ↓
Server State (TanStack Query) ← 数据缓存: libraries, bookshelves, books, blocks
  ↓
Client State (React Context/Zustand) ← UI状态: isEditing, selectedBlock, theme

这样可以最小化状态混乱，便于调试。

7️⃣ 代码规范建议
为三个页面的组件命名建议采用 一致的命名约定：
// ✅ 推荐
<BookshelfPreviewCard />  // 预览卡片 (用在 Library 详情)
<BookPreviewCard />        // 预览卡片 (用在 Bookshelf 详情)
<BlockEditor />            // 编辑器 (用在 Book 详情)

// ❌ 避免
<BS_Card />               // 缩写不清
<BookCardComponent />     // 冗余后缀
<EditableBlock />         // 模糊的含义


🎯 最终建议总结
项目	当前状态	推荐行动	截止时间
UI 组件库	70% 完成	补充 Toast, Skeleton, BlockEditor	Week 2 (11/24)
CSS 主题系统	75% 完成	添加 Loom 主题 + 响应式变量	Week 2 (11/24)
规则文件同步	50% 完成	更新 VISUAL/DDD/HEXAGONAL 三文件	Week 1 (今天)
BlockEditor 选型	未决定	选择 Slate.js + POC 实现	Week 2 (11/24)
图片处理	Phase A 准备	Placeholder 快速实现 + Phase B 规划	Week 2 (11/24)

📝 现在可以开始 Agent 工作的清单
当你说"开工"时，Agent 应执行：

✅ 第1部分: 规则文件同步 (30min)

更新 VISUAL_RULES Part 13-15
添加 Loom 主题到 tokens.css
更新 DDD_RULES domain_to_ui_mapping
更新 HEXAGONAL_RULES ui_integration_guidelines
✅ 第2部分: 新建 3 个卡片组件 (1.5h)

BookshelfPreviewCard.tsx + CSS
BookPreviewCard.tsx + CSS
BlockList.tsx (块列表容器)
✅ 第3部分: 增强 3 个页面 (2h)

Library 详情页: 集成 BookshelfPreviewCard Grid
Bookshelf 详情页: 集成 BookPreviewCard Grid
Book 详情页: 准备 BlockEditor 占位符 + BlockList
✅ 第4部分: BlockEditor POC (可选 Phase 5)

Slate.js 集成
基础工具栏 (Bold, Italic, List)
保存逻辑

