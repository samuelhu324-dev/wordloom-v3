---
id: adr-bookshelf-overview-stability
title: Bookshelf Overview 稳定性改造
status: draft
date: 2025-12-19
related:
  - ck: ck-bookshelf-overview-regression
  - spec: spec-bookshelf-overview
---

## 1. 背景（Context）

Bookshelf Overview（`BookshelfMainWidget`）是 Library 详情页中最重要的子区域之一，用于概览当前 Library 下所有书橱的数量、状态与容量。现状与痛点：

- 仅提供 List 视图，未实现 Grid；组件内部仍遗留视图/偏好持久化代码路径的假设，需要明确关闭。
- 排序（最近更新 / 名称 A-Z / 书本数量）与状态筛选（All / Active / Archived）存在，但行为缺少统一规范，空态文案也未固定。
- 书橱数量上限（100 个）与预警阈值（80 个）的 UI 提示存在，但未被系统性验证，容易在样式或逻辑调整时回归。
- 错误状态（后端请求失败）有专门的错误块，但缺乏与其他区域的隔离性约束描述。
- 书橱卡片不展示 description，但后续可能接入书橱级 Pin/标签等能力，需要在 Overview 层面预留稳定性要求与 ID 管理。

因此，需要一份与 Library Overview 类似的稳定性 ADR，用来约束 Bookshelf Overview 的数据流、交互与回归策略。

## 2. 决策与目标（Decision / Goals）

1. **统一行为约束**：明确 Bookshelf Overview 在 List 视图下的加载、排序与筛选一致性要求，并通过 SPEC 与 checklist 固化（无 Grid/偏好持久化）。
2. **容量与错误可观测**：保证书橱数量上限与预警提示、错误状态展示都有明确的 UX 标准和验收项。
3. **ID 治理**：为 Bookshelf Overview 建立独立的 ID 索引文件 `bookshelf-overview-ids.json`，所有回归项以 `BSH-OVW-*` 命名并在 ck/spec/adr 中互相引用。
4. **为未来能力预留空间**：提前预留 Pin 排序与标签展示等 ID，避免后续能力堆叠时缺乏追踪。

## 3. 技术与产品方案概要

### 3.1 数据与状态管理

- 保持 Bookshelf 列表由上层（例如 Library 详情页）以 props 方式传入，`BookshelfMainWidget` 只负责视图层过滤与排序，不再自行触发列表请求。
- 不做本地偏好持久化；排序与筛选为内存态，进入页面时采用默认值（最近更新 + All）。

### 3.2 交互与展示

- Header 区域展示：当前书橱总数 + 上限进度条 + 接近/达到上限时的文案。
- Controls：
  - Sort 下拉：支持 `updated_desc` / `name_asc` / `book_count_desc`，在 `derivedBookshelves` 里统一处理；
  - Status Filter 下拉：`all` / `active` / `archived`（无 Basement 入口）。
- 列表区域：
  - 使用 `BookshelfList` 渲染 List 布局；
  - 空态（无数据或筛选后无结果）统一文案：`No bookshelves yet`；
  - 书橱卡片当前不展示 description。
- 错误区域：
  - 当上层传入 `error` 时，渲染包含 HTTP 状态码与 detail 的红色提示块，并渲染空列表作为降级；
  - 不影响页面中其他 widget 的正常渲染。

### 3.3 容量与告警策略

- `MAX_BOOKSHELVES = 100`，`WARN_THRESHOLD = 80`：
  - `bookshelfTotalCount >= WARN_THRESHOLD` 时展示进度条 + 预警文案；
  - `bookshelfTotalCount >= MAX_BOOKSHELVES` 时禁用 "新建书橱" 按钮，并在 tooltip/title 中给出原因说明。
- 回归项通过 `BSH-OVW-LimitWarningVisible` 与 `BSH-OVW-LimitReachedDisabled` 进行覆盖。

### 3.4 Checklist / ID 对应关系

- 回归清单：[backend/storage/assets/checklist/regression/ck-bookshelf-overview-regression.md](backend/storage/assets/checklist/regression/ck-bookshelf-overview-regression.md)。
- ID 索引：[backend/storage/assets/checklist/index/bookshelf-overview-ids.json](backend/storage/assets/checklist/index/bookshelf-overview-ids.json)。
- 行为规范 SPEC：[backend/storage/assets/spec/spec-bookshelf-overview.md](backend/storage/assets/spec/spec-bookshelf-overview.md)。

## 4. 验收标准（Acceptance）

最低验收要求：

- `BSH-OVW-LoadingVisible`、`BSH-OVW-CreateVisible`、`BSH-OVW-BookshelfClickable`、`BSH-OVW-StatusMetaAccurate`、`BSH-OVW-SortOptionsWork`、`BSH-OVW-StatusFilterWorks`、`BSH-OVW-LimitWarningVisible`、`BSH-OVW-ErrorBannerVisible`、`BSH-OVW-NoErrorsInConsole` 在 ck-run 中全部通过。
- 未实现的未来能力（如 `BSH-OVW-PinOrdering`、`BSH-OVW-TagsDisplay`）在 ck-run 中显式标记为 N/A，并关联后续需求/issue。

## 5. 风险与回滚

- **容量逻辑错误**：若 MAX/WARN 阈值或判断条件被误改，可能出现无法创建或无预警提示。回滚方式：恢复常量与判断逻辑到本 ADR 描述的版本。
- **错误状态未隔离**：若错误 UI 未正确渲染或抛出异常，可能影响整页渲染。回滚方式：恢复原有 error 分支渲染逻辑，并在 BookshelfMainWidget 外层增加防御性 ErrorBoundary（如有必要）。

## 6. 后续工作与 Future IDs

- 当书橱级 Pin/标签能力上线时，需要：
  - 更新 SPEC 第 3 章交互规范；
  - 将 `BSH-OVW-PinOrdering`、`BSH-OVW-TagsDisplay` 的 status 从 `planned` 调整为 `active`，并增加对应回归检查内容；
  - 视情况增加自动化测试覆盖。
