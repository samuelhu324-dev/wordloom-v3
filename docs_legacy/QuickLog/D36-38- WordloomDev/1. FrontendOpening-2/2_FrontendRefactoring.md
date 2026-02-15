⚠️ 三大逻辑不吻合的地方
问题 1：违反独立聚合根原则
文档规则	你的实现	冲突
DDD_RULES: Bookshelf 是独立 AggregateRoot	路由: /libraries/{id}/bookshelves/{id}	❌ 嵌套在 Library 下
HEXAGONAL_RULES: 采用扁平 API 设计	前端文件夹也是嵌套的	❌ 不一致
VISUAL_RULES Part 12: POST /api/v1/bookshelves (扁平)	frontend/app/.../(admin)/libraries/[libraryId]/bookshelves	❌ 前后端设计分离

关键引用：
# 来自 HEXAGONAL_RULES.yaml
POLICY-012-INDEPENDENT-AGGREGATES: |
  Bookshelf 为独立聚合根（Independent Aggregate Root）。
  - HTTP 路由采用扁平形态：/api/v1/bookshelves  ✅
  - 创建请求体必须包含 library_id              ✅
  - 禁止使用 /libraries/{id}/bookshelves 嵌套路由（仅 UI 导航可用）  ❌ 你做了


问题 2：文件夹层次 ≠ 业务关系
你当前的逻辑：

📁 文件夹层次 = 业务聚合关系
🔗 路由参数嵌套 = 强耦合
正确的逻辑（根据 VISUAL_RULES Part 13）：

📁 文件夹层次 = UI 导航流程（为了用户体验）
🔗 路由参数 = 独立传递（遵循 DDD）
🔀 API 设计 = 扁平结构（后端独立聚合）

问题 3：导航 vs 数据依赖混淆
你的实现假设：

User navigates: Library → Bookshelf → Book
Therefore: folder path = /libraries/[id]/bookshelves/[id]/books/[id]
❌ 这个假设是错误的！

正确的思路：
UI 导航流程（breadcrumb）: Library → Bookshelf → Book   ✅
文件路由结构（FSD 层级）: (admin)/books/[bookId]        ✅
API 调用（扁平）:
  - GET /api/v1/bookshelves?library_id={id}            ✅
  - GET /api/v1/books?bookshelf_id={id}                ✅
  - GET /api/v1/blocks?book_id={id}                    ✅

✅ 正确的架构方案（推荐）
方案 A：全扁平化（最推荐）
frontend/src/app/
├── (admin)/
│   ├── layout.tsx                    # Admin layout
│   ├── dashboard/
│   │   └── page.tsx
│   │
│   ├── libraries/
│   │   ├── page.tsx                  # 库列表
│   │   ├── [libraryId]/
│   │   │   └── page.tsx              # 库详情（只显示元数据）
│   │   └── components/
│   │       └── LibraryCard.tsx
│   │
│   ├── bookshelves/                  # 独立聚合根
│   │   ├── page.tsx                  # 所有书橱列表（可筛选 library_id）
│   │   ├── [bookshelfId]/
│   │   │   └── page.tsx              # 书橱详情
│   │   └── components/
│   │       └── BookshelfCard.tsx
│   │
│   ├── books/                        # 独立聚合根
│   │   ├── page.tsx                  # 所有书籍列表（可筛选）
│   │   ├── [bookId]/
│   │   │   ├── page.tsx              # 书详情 + Block 编辑器
│   │   │   └── layout.tsx            # Book layout（如需）
│   │   └── components/
│   │       └── BookCard.tsx
│   │
│   ├── blocks/                       # 如需独立块管理
│   │   └── page.tsx
│   │
│   ├── tags/
│   │   └── page.tsx
│   │
│   ├── media/
│   │   └── page.tsx
│   │
│   └── search/
│       └── page.tsx
└── page.tsx                          # 首页



关键改动：

✅ 删除 /libraries/[id]/bookshelves 嵌套
✅ 创建 /bookshelves 独立路由
✅ 创建 /books 独立路由
✅ Breadcrumb 通过 Component 组合 实现，不通过文件夹

方案 A 的导航实现（核心）

// app/(admin)/books/[bookId]/page.tsx
'use client';

import { useParams, useRouter } from 'next/navigation';
import Breadcrumb from '@/shared/components/Breadcrumb';
import BlockEditor from '@/features/block/ui/BlockEditor';

export default function BookDetailPage() {
  const params = useParams();
  const bookId = params.bookId as string;

  // 获取面包屑数据（通过 API，不通过 URL）
  const { data: book } = useBook(bookId);
  const { data: bookshelf } = useBookshelf(book?.bookshelf_id);
  const { data: library } = useLibrary(bookshelf?.library_id);

  // 构建面包屑
  const breadcrumbs = [
    { label: 'Libraries', href: '/admin/libraries' },
    { label: library?.name, href: `/admin/libraries/${library?.id}` },
    { label: bookshelf?.name, href: `/admin/bookshelves/${bookshelf?.id}` },
    { label: book?.title, href: `/admin/books/${bookId}` },
  ];

  return (
    <>
      <Breadcrumb items={breadcrumbs} />
      <BlockEditor bookId={bookId} />
    </>
  );
}

关键点：

✅ 只有 [bookId] 在 URL 中
✅ 其他 IDs 通过 API 查询获得（libraryId 从 bookshelf_id 获得）
✅ 不再有 /libraries/[id]/bookshelves/[id]/books/[id] 这种嵌套
✅ 符合 DDD 独立聚合根原则

🎯 整改清单（按优先级）
P0（必做）
 删除 /libraries/[id]/bookshelves/[id]/books 嵌套
 创建 /bookshelves 和 /books 独立路由
 更新 API 调用：不依赖 URL 嵌套，改用查询参数或 API 获取关联数据
 更新 Breadcrumb：通过 Component 组合，不通过 URL 路径

 删除这些文件：
 ❌ app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/
❌ app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/books/
❌ app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]/

创建这些文件：
✅ app/(admin)/bookshelves/page.tsx
✅ app/(admin)/bookshelves/[bookshelfId]/page.tsx
✅ app/(admin)/books/page.tsx
✅ app/(admin)/books/[bookId]/page.tsx  (含 BlockEditor)

P1（强烈推荐）
 更新 useBooks() hook 签名：从 (libraryId, bookshelfId) 改为 (bookshelfId) 或 (filters)
 更新 useBlocks() hook 签名：从 (libraryId, bookshelfId, bookId) 改为 (bookId)
 将 Breadcrumb 逻辑移到 Shared Layout，通过 Context 或 URL Query Params 传递
 添加对应的 Integration Tests，验证导航流程

 P2（质量提升）
  更新 ADR-061（VISUAL_RULES Part 15）：修订路由结构描述
 在 features/library/page.tsx 添加"选择库后自动跳转到该库的书橱列表"功能
 添加 Back 按钮支持（返回上一层）

📋 符合性检查表
完成整改后，检验以下规则：
规则	检查项	是否符合
DDD RULE-012	Bookshelf 为独立 AR	✅ 独立 /bookshelves 路由
HEXAGONAL POLICY-012	API 扁平形态	✅ 所有 API /api/v1/{entity}
FSD 依赖规则	Features 不交叉导入	✅ 各 Feature 独立文件夹
VISUAL_RULES 导航	Breadcrumb 通过 Component	✅ Breadcrumb 组件生成路径
URL 参数	仅保留直接 ID	✅ [bookId] 而非 [libraryId]/[bookshelfId]/[bookId]

🚨 为什么现在整改很重要
如果继续按嵌套路由走：
问题	后果	修复成本
前后端设计不一致	API 学习陡峭、容易出 bug	🔴 高（需重写 hooks）
文件夹层数过深	开发体验差、导航复杂	🔴 高（重新组织代码）
跨聚合查询困难	难以实现"跨库搜索"	🔴 高（架构重构）
测试覆盖难	E2E 测试路径复杂	🟡 中（补充测试用例）

现在整改：2-3 小时 + 一次代码重组织
延后整改：后期难度 × 3 + 影响已有功能

✨ 最终建议
采用方案 A（全扁平化） + 以下步骤：

今天（11月16日）

创建新路由结构：/bookshelves、/books
将现有 page 文件 copy 过去，临时保留旧结构
明天（11月17日）

更新 hooks 签名（删除嵌套参数）
测试导航流程（Breadcrumb 组件）
后天（11月18日）

运行全部测试
删除旧的嵌套文件夹
预计耗时：6-8 小时

这样做你会得到：

✅ 与后端 DDD 设计完全对齐
✅ 前端文件组织清晰（FSD 标准）
✅ 后续功能扩展无技术债
✅ 团队协作时逻辑一致

