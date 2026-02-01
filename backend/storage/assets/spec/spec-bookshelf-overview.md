---
id: spec-bookshelf-overview
title: Bookshelf Overview 行为规范
status: draft
version: 0.1.0
updated: 2025-12-19
relatedAdr:
  - adr-bookshelf-overview-stability
relatedChecklist:
  - ck-bookshelf-overview-regression
---

## 1. 范围（Scope）

**In scope**
- Library 详情页中嵌入的 `BookshelfMainWidget` 与 `BookshelfList` 组件；
- List 视图下的排序、状态筛选、书橱数量上限提示、错误展示；
- 通过 "新建书橱" 对话框创建书橱的流程与结果反馈。

**Out of scope**
- 单个书橱详情页与书本列表（由 Book/Bookshelf 其他 SPEC 覆盖）；
- Basement 中已删除书橱的恢复流程；
- 书橱级 Pin、标签等尚未实现的高级能力（见 Future Work）。

## 2. 页面结构

1. **Header 区块**：
  - 标题：当前 Library 下的 "书橱"；
  - 书橱数量徽章：`当前数量/MAX_BOOKSHELVES`（如 `12/100 书橱`）；
  - 当数量达到预警阈值时显示容量进度条与提示文案。
2. **Controls**：
  - Sort 下拉：`最近更新` / `名称 A-Z` / `书本数量`；
  - 状态筛选下拉：`全部状态` / `仅 Active` / `仅 Archived`；
  - `新建书橱` 主按钮（达到上限时禁用）。
3. **列表区域**：
  - 使用 `BookshelfList` 渲染书橱卡片（仅 List 布局）；
  - 无数据或过滤后无结果时展示统一空态文案：`No bookshelves yet`。
4. **错误区域**：
  - 当 `error` 存在时，在 Header 下方展示红色错误提示块，并渲染空列表。

## 3. 交互规范

### 3.1 加载（BSH-OVW-LoadingVisible）
- 默认以 List 视图加载，不做 Grid 切换；
- 排序与筛选为内存态，进入页面时默认：`最近更新` + `All`；
- 列表正常渲染，无空白或未处理异常。

### 3.2 创建书橱（BSH-OVW-CreateVisible）
- 点击 `新建书橱` 打开创建对话框（复用 LibraryForm）：
  - 必填字段：名称；
  - 可选字段：简介、标签；
  - Library ID 自动带入。
- 创建成功后：
  - 对话框关闭并展示成功 toast；
  - Bookshelf 列表与数量统计立即更新，无需手动刷新；
  - 若达到容量上限，则按钮随即禁用并更新文案。

### 3.3 列表展示与点击（BSH-OVW-StatusMetaAccurate, BSH-OVW-BookshelfClickable）
- 书橱卡片展示：名称、状态（Active/Archived）、书本数量和最近更新时间（不展示 description）。
- 元信息与后端数据保持一致；
- 点击任意卡片触发 `onSelectBookshelf(id)`，由上层决定导航行为。

### 3.4 排序与筛选（BSH-OVW-SortOptionsWork, BSH-OVW-StatusFilterWorks）
- 排序：
  - `最近更新`：按 `updated_at` 降序排列；
  - `名称 A-Z`：按名称使用汉字/拼音排序（使用 `localeCompare`）；
  - `书本数量`：按 `book_count` 降序排序。
- 筛选：
  - `全部状态`：包含所有书橱；
  - `仅 Active`：状态为 active；
  - `仅 Archived`：状态为 archived；
- 空态：无数据或筛选后无结果时，展示统一文案 `No bookshelves yet`。

### 3.5 容量与告警（BSH-OVW-LimitWarningVisible, BSH-OVW-LimitReachedDisabled）
- `MAX_BOOKSHELVES = 100`，`WARN_THRESHOLD = 80`：
  - 当数量 >= WARN_THRESHOLD 时展示进度条与提示文案；
  - 当数量 >= MAX_BOOKSHELVES 时：
    - `新建书橱` 按钮禁用；
    - 按钮文案与 tooltip 中说明原因（达到上限）。

### 3.6 错误与降级（BSH-OVW-ErrorBannerVisible, BSH-OVW-ErrorStateIsolated, BSH-OVW-NoErrorsInConsole）
- 当上层传入 `error` 时：
  - 在 Header 下方渲染错误提示块，包含 `HTTP {status}` 与后端 detail（如有）；
  - BookshelfList 接收空数组并渲染空列表，不抛出额外异常；
  - 其他 widget（如 Books、Basement）保持正常工作。
- 正常操作过程中浏览器控制台不应出现未捕获错误，如有则视为 `BSH-OVW-NoErrorsInConsole` 失败。

## 4. Checklist 对照

| 能力 | Checklist ID | 备注 |
| --- | --- | --- |
| 加载 | BSH-OVW-LoadingVisible | List 视图，默认最近更新 + All |
| 创建流程 | BSH-OVW-CreateVisible | 新建后列表与计数同步 |
| 展示与点击 | BSH-OVW-StatusMetaAccurate / BSH-OVW-BookshelfClickable | 无 description，状态/数量准确 |
| 排序与筛选 | BSH-OVW-SortOptionsWork / BSH-OVW-StatusFilterWorks | 无 Basement，统一空态文案 |
| 容量与告警 | BSH-OVW-LimitWarningVisible / BSH-OVW-LimitReachedDisabled | 上限 100 逻辑 |
| 错误与质量 | BSH-OVW-ErrorBannerVisible / BSH-OVW-ErrorStateIsolated / BSH-OVW-NoErrorsInConsole | 降级与稳定性 |

## 5. Verification（ck-run 指南）

- 每次回归 Bookshelf Overview 时执行 `ck-bookshelf-overview-regression`，并在对应 ck-run 文件中记录每条检查的结果（通过 / 失败 / N/A）。
- 若能力尚未实现（如 Pin 排序、标签展示），须在 ck-run 中写明 N/A 与关联的需求/issue ID。

## 6. Future Work

- **书橱 Pin 与排序（BSH-OVW-PinOrdering）**：
  - 预计引入书橱级 Pin 字段，在 Overview 中采用 pinned-first 排序；
  - 具体交互方案将通过新的 ADR 更新本 SPEC。
- **书橱标签展示（BSH-OVW-TagsDisplay）**：
  - 统一书橱标签的 chips / 占位文案 / 最大展示数量；
  - 与 Library Overview 的标签规范对齐后，更新本规范与回归清单。