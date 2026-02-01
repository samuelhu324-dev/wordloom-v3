---
id: ISS-BSH-OVW-GROUPING-PIN-EMPTYSTATE
title: Bookshelf Overview 分层/Pin 顺序与空态文案对齐
status: open
created_at: 2025-12-19
resolved_at: 
related_checks:
  - BSH-OVW-StatusFilterWorks
  - BSH-OVW-SortOptionsWork
  - BSH-OVW-PinOrdering
  - BSH-OVW-LoadingVisible
---

## 背景

在 Library Overview 已经完成 “Pinned 分层精简为 All / Archived、Pin 顺序复用标签逻辑、空态文案统一” 等一系列稳定性改造之后，Bookshelf Overview 目前仍存在几处不一致：

1. **分层结构不一致**：Library 已收敛为 All Libraries / Archived Libraries 两层，而 Bookshelf 仍然沿用旧的 Pinned / All / Basement 之类的层级设想，实际产品上希望仅保留 All Bookshelves 与 Archived Bookshelves 两个层级。
2. **Pin 顺序未复用 Library 逻辑**：Library 卡片已经通过 `Pin/Unpin` + React Query 缓存刷新实现 pinned-first 且即时生效；Bookshelf 列表目前没有 Pin 顺序逻辑，后续一旦提供 Pin 能力，希望直接复用 Library 卡片的实现与标签规范。
3. **空态文案不统一**：Library/Books 区域已经统一使用 “No X yet.” 风格的空态；Bookshelf 在不同筛选状态（如 Archived）下仍存在旧文案，期望统一为 `No bookshelves yet`。
4. **容量/错误场景难以手工回归**：与 Library 类似，书橱接近上限 / 达到上限以及后端错误分支较难靠造数与环境手工覆盖，需要通过脚本或自动化测试来保证回归质量。

## 影响

- 用户在 Library 与 Bookshelf 之间切换时，分层与空态体验不一致（Pinned 层级多余、Archived 命名不统一、空态文案风格不同）。
- 一旦上线书橱 Pin 能力，如果不复用 Library 的 pinned-first 实现，很容易出现排序/分组行为不一致的问题，给回归与产品说明带来额外成本。
- 容量预警、上限禁止创建、错误降级等场景手工难以稳定复现，若缺乏脚本/自动化支撑，极易在后续改动中回归。

## 目标

1. Bookshelf Overview 分层简化为 **All bookshelves / Archived bookshelves**，取消 Pinned 层级，与 Library 的 All / Archived 语义对齐。
2. 未来引入书橱 Pin 能力时，列表采用 **pinned-first** 排序，并直接复用 Library 卡片的 Pin/Archive + 缓存刷新实现，以减少新发明逻辑。
3. 所有 Bookshelf 状态筛选（All / Active / Archived）在无结果时统一展示 `No bookshelves yet` 文案（包括截图中的 Archived 场景），与 Library/Books 的空态风格保持一致。
4. 为容量与错误场景补充 **可重复的验证手段**（脚本或自动化测试），避免只能依赖手工造数。

## 建议方案

### 1. 分层与筛选

- 前端不再渲染 Pinned 层级，Bookshelf Overview 仅保留：
  - All bookshelves（默认视图）；
  - Archived bookshelves（仅展示 Archived 书橱）。
- `BSH-OVW-StatusFilterWorks` 对应的下拉仅保留 All / Active / Archived 三种状态，不再暴露 Basement 或 Pinned 相关选项；
- 在 SPEC 中更新分层描述，与 `ISS-LIB-GROUPING-SIMPLIFY` 的方案保持一致。

### 2. Pin 排序复用 Library 逻辑

- 待书橱支持 Pin 字段后：
  - 引入 `BSH-OVW-PinOrdering`：
    - 同一分组（All / Archived）内，已 Pin 的书橱排在未 Pin 之前；
    - Pin/Unpin 操作后，通过 React Query 缓存写入 + 可选 invalidate 的方式即时刷新 UI；
  - 实现上直接复用 Library 卡片中 `Pin/Unpin` 的数据流与排序 comparator，避免为 Bookshelf 单独写一套逻辑；
  - 标签展示（tags chips、占位、最大展示数量）比照 Library 的 `LIB-OVW-Tags*` 规范，在 Bookshelf 标签能力落地后开启 `BSH-OVW-TagsDisplay` 并补充自动化回归。

### 3. 空态文案统一

- 将 Bookshelf Overview 在以下场景的空态文案统一为：`No bookshelves yet`：
  - Library 下没有任何书橱；
  - 筛选为 Active 而当前库只有 Archived 书橱；
  - 筛选为 Archived（截图 1 场景）且当前无归档书橱；
  - 错误 / loading 以外的正常空结果情况。
- 对应回归项：在 `BSH-OVW-StatusFilterWorks` 中明确要求 All / Active / Archived 空结果统一文案，避免出现 “No bookshelves in this library yet. Create one first.” 等旧版本字段。

### 4. 无法手工测试的场景如何覆盖？

针对截图 2（容量与告警）和截图 3（错误与降级）这类 **难以通过手工造数稳定复现** 的场景，建议：

1. **临时脚本造数**（后端 / 管理脚本）：
   - 在 `backend/scripts` 下增加一次性脚本（例如 `seed_bookshelves_limit_cases.py`），为指定 Library 批量创建 80、100 个书橱，用于本地或测试环境验证：
     - `>= 80` 时进度条与预警文案；
     - `>= 100` 时按钮禁用与 tooltip 文案。
   - 脚本执行完即可清理对应 Library，避免污染长期数据。
2. **自动化测试补位**：
   - 在 `frontend/tests/e2e` 中新增 Bookshelf Overview 用例：
     - 通过 API/seed 数据预置 80+ 书橱，截图校验进度条与文案（对应 `BSH-OVW-LimitWarningVisible`）；
     - 预置 100+ 书橱，校验新建按钮禁用状态与 tooltip（对应 `BSH-OVW-LimitReachedDisabled`）；
     - 模拟后端返回 4xx/5xx 时的 Error boundary 展示与降级行为（对应 `BSH-OVW-ErrorBannerVisible` / `BSH-OVW-ErrorStateIsolated`）。
   - 与 ck-run 文件关联：在 `ck-run-bookshelf-overview-YYYY-MM-DD.md` 中注明上述检查项由自动化覆盖，手工仅做抽查。
3. **ck-run 记录策略**：
   - 当前手工难以执行的条目在 ck-run 中暂记为 `N/A (covered by automation / script only)`；
   - 等自动化用例或造数脚本落地后，将状态更新为 `pass` 或具体失败原因。

## 状态

- 2025-12-19：记录 Bookshelf 分层/Pin/空态/容量与错误测试上的差异与风险，issue 新建为 open，等待前端与自动化同学认领具体实现。
