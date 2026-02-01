# ADR-074: Bookshelf UI + Flat Endpoints (B 方案)

- Status: Accepted
- Date: 2025-11-19
- Authors: Wordloom Core
- Related: ADR-057, ADR-060, ADR-069, ADR-071, ADR-072

## Context
- 前端与后端端口统一：Backend 30001，Frontend 30002。
- CORS 已调整，允许 `http://localhost:30002` 与 `http://127.0.0.1:30002` 访问后端。
- 架构采用 Hexagonal + DDD；聚合根独立，HTTP 路由采用平铺风格（flat endpoints）。
- 需求：实现 Bookshelf UI，包含两种列表模式（网格/列表），卡片包含封面、标题、说明；在 Library 详情内支持创建与筛选。

## Decision
- 选择 B 方案：Bookshelf 为独立聚合根（Independent Aggregate Root）。
  - 后端路由采用平铺：`/api/v1/bookshelves`。
  - 创建时必须提供 `library_id`；查询时使用 `?library_id={id}` 过滤。
- UI 约束：
  - Bookshelf 的创建入口放在 Library 详情页范围内，避免跨库误创建。
  - 全局页面仍提供 `/admin/bookshelves` 平铺视图，用于检索与跳转。
- 端口与环境：
  - Backend: `http://localhost:30001`（Uvicorn/FastAPI, prefix `/api/v1`）。
  - Frontend: `http://localhost:30002`（Next.js 14）。
  - CORS: 允许 30002 源；环境变量前端使用 `NEXT_PUBLIC_API_BASE=http://localhost:30001` 与 `NEXT_PUBLIC_API_PREFIX=/api/v1`。

## Consequences
- Pros:
  - 聚合根独立，扩展性强；前后端均保持路由平铺的一致性；UI 可按 Library 语义进行范围化创建。
- Cons:
  - 需要在创建/筛选时明确传递 `library_id`；前端需要在上下文中维护当前 library。

## API
- GET `/api/v1/bookshelves?library_id={libraryId}`：按库查询书架。
- POST `/api/v1/bookshelves`：创建书架（body 必须包含 `library_id`）。
- 其它（获取单个/更新/删除）维持平铺风格：`/api/v1/bookshelves/{bookshelfId}`。

## UI 实现（前端）
- 类型与 API：
  - `src/entities/bookshelf/types.ts`
  - `src/entities/bookshelf/api.ts`（Axios 适配，base 由 `NEXT_PUBLIC_API_BASE + NEXT_PUBLIC_API_PREFIX` 构成）
  - `src/entities/bookshelf/hooks.ts`（TanStack Query：useBookshelves, useCreateBookshelf）
- 组件：
  - `src/entities/bookshelf/ui/BookshelfCard.tsx`（封面、标题、描述）
  - `src/entities/bookshelf/ui/BookshelfGrid.tsx`（网格）
  - `src/entities/bookshelf/ui/BookshelfList.tsx`（列表）
  - `src/entities/bookshelf/ui/BookshelfForm.tsx`（创建表单，需 `libraryId`）
- 页面与挂件：
  - `/admin/bookshelves/page.tsx`（全局平铺视图）
  - `/admin/libraries/[libraryId]/bookshelves/page.tsx`（库范围视图 + 创建）
  - 可选 widget：`src/widgets/BookshelfWidget.tsx` 用于嵌入 Library 详情页。

## Migration & Ops
- 确认后端 CORS 包含：`http://localhost:30002`, `http://127.0.0.1:30002`。
- 前端 `.env.local`：
  - `NEXT_PUBLIC_API_BASE=http://localhost:30001`
  - `NEXT_PUBLIC_API_PREFIX=/api/v1`
- 后端保持 API 前缀 `/api/v1` 与端口 30001。

## Validation
- 手动验证（本地）：
  - 启动后端（30001），访问 `GET /api/v1/health` 返回 200。
  - 启动前端（30002），在 Library 详情内创建 Bookshelf 成功，网络请求为 `POST /api/v1/bookshelves`，body 包含 `library_id`。
  - `GET /api/v1/bookshelves?library_id=...` 返回正确列表，UI 网格/列表切换正常。

## Notes
- 本 ADR 与 ADR-071 一致，强调平铺路由与独立聚合；仅界定 UI 范围化创建策略。
- 实施顺序：
  1) 规则文件同步（端口、CORS、路由风格）。
  2) 前端实体/接口/Hook。
  3) 组件与页面。
  4) 校验与微调性能（网络与渲染）。
