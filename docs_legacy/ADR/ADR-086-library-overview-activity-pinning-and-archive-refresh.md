# ADR-086: Library Overview Activity, Pinning, and Archive Refresh

Date: 2025-11-22
Status: Accepted
Authors: Backend / Frontend / Architecture
Supersedes: (None)
Related: DDD_RULES v3.10, HEXAGONAL_RULES v1.9, VISUAL_RULES v2.6, ADR-082

## Context
Library 页面原有实现仅按 `updated_at` 排序且缺乏置顶/归档能力：
- 列表无法突出最近活跃或关注的 Library，导致高频使用的工作区在列表中淹没。
- 无置顶元数据与分区，前端无法在 UI 顶部固定关键库。
- 归档操作缺失，历史项目与活跃项目混在同一列表，干扰日常导航。
- 浏览行为没有写入，难以统计使用频率。
- 多处业务逻辑已在 Plan 20 Option A 中规划：last_activity 排序、Pinned 段落、Archive toggle、即时 view 计数。

## Forces / Drivers
- **排序精准性**：需要统一的 `last_activity_at` 更新时间戳，涵盖 Bookshelf / Book / Block 写操作。
- **关注库曝光**：需提供 pinned 段落与顺序字段，支持后续拖拽排序。
- **生命周期管理**：归档库默认隐藏，仅在显式要求时显示。
- **数据可观测性**：需记录浏览次数与最后浏览时间，便于未来仪表盘与推荐逻辑。
- **端到端一致性**：后端、前端、文档需同步，避免前后端字段不一致。

## Decision
采纳 Plan 20 Option A，交付以下能力：
- 数据库迁移 `018_library_activity_and_sort.sql`：新增 `last_activity_at`、`pinned`、`pinned_order`、`archived_at`、`views_count`、`last_viewed_at` 列，并创建触发器 `touch_library_activity` 在 Bookshelf / Book / Block CRUD 后刷新活动时间。
- Router `GET /api/v1/libraries` 支持 `sort`（last_activity|views|created|name）、`pinned_first`、`include_archived` 参数，默认 pinned 段置前、last_activity 降序。
- `PATCH /api/v1/libraries/{id}` 支持 `pinned`、`pinned_order`、`archived` 轻量操作；`POST /libraries/{id}/views` 立即持久化视图数据。
- Repository `SQLAlchemyLibraryRepository.list_overview` 实现排序/过滤/分组逻辑，`save()` 同步新字段。
- 前端 LibraryMainWidget 增加排序选择、归档开关、偏好持久化；LibraryList / LibraryCard 渲染 Pinned / Archived 段落、快速置顶/归档按钮、活动与浏览指标。
- 三份规则文档更新：记录新字段、索引、UI 规则与迁移状态。

## Implementation Summary
Backend:
- Migration `backend/api/app/migrations/018_library_activity_and_sort.sql`（WSL2 PostgreSQL 已执行；旧迁移 001/004/017 重复失败可忽略）。
- Domain `Library` 聚合新增字段与方法：`set_pinned`、`archive`、`unarchive`、`touch_activity`、`record_view`。
- Use cases：`UpdateLibraryUseCase`、`RecordLibraryViewUseCase` 接受新参数并保存。
- Router：`list_libraries` 参数化排序；新增 `POST /libraries/{id}/views`；patch 支持 pinned/archive。
- Repository：`list_overview` 组合排序条件，`save()` 写入新字段，降级执行 pinned tie-breaker。

Frontend:
- `LibraryMainWidget`：排序下拉、归档切换、本地存储偏好。
- `LibraryList`：按 pinned / active / archived 分区；快速置顶时分配 `pinned_order`；归档按钮即时更新。
- `LibraryCard`：metric 行显示 last_activity 与 views；footer 显示最后浏览；按钮 stopPropagation 避免误计数。
- API 层：`useQuickUpdateLibrary` 支持部分更新；记录视图 mutation。

Documentation:
- `HEXAGONAL_RULES.yaml`、`VISUAL_RULES.yaml`、`DDD_RULES.yaml` 均追加相应规则、索引、状态追踪。
- ADR-086（本文）记录决策背景与后续计划。

## Alternatives Considered
1. **仅前端排序**：只在客户端计算 last_activity，不改数据库。风险：数据不一致、背离后续高并发需求。
2. **延迟写视图计数**：通过队列异步聚合。当前阶段读写量低，直接同步写可简化实现，未来可替换。
3. **Pinned 顺序使用浮点**：改用 Fractional Index。现阶段非拖拽，仅需整数；后续可切换为 Fractional Index。

## Consequences
Positive:
- Library 列表突出活跃与关注库，归档列表默认折叠。
- 触发器统一刷新活动时间，消除“手动 touch”遗漏。
- 前后端字段一致，便于下一步实现拖拽排序与仪表盘。

Trade-offs:
- `last_activity_at` 当前通过触发器修改 `updated_at`，会增加额外写操作；需监控写放大。
- 归档/置顶按钮为快速操作，尚未提供撤销/提示，未来需 UX 优化。
- `pinned_order` 目前简单减一插入，置顶数量大时需再平衡。

## Rollback Plan
如迁移导致问题：
1. 停止使用新字段（前端降级隐藏排序 UI）。
2. 回滚迁移：删除新增列与触发器，保留原逻辑。
3. Repository 与 router 恢复旧实现（只按 `updated_at` 排序，没有 pinned/archived 参数）。
4. 前端移除新控件；规则文档回滚。

## Future Work
- 实现 pinned 拖拽排序 → 引入 Fractional Index 与批量更新 use case。
- 归档库只读限制：后端 enforce 写操作禁止；UI 提示。
- 视图计数上报与分析仪表盘。
- 多用户回归时，结合 `user_id` 过滤与 pinned_order 序列化策略。

## Status Links
- Migration: `backend/api/app/migrations/018_library_activity_and_sort.sql` 已在 WSL2 环境执行。
- Rules: DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES Nov 22 更新已记录。
- Frontend: `LibraryMainWidget.tsx`, `LibraryList.tsx`, `LibraryCard.tsx`, `model/hooks.ts`。

Accepted: 2025-11-22.
