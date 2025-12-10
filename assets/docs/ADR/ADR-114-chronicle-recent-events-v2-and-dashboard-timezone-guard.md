# ADR-114: Chronicle Recent Events v2 & Dashboard Timezone Guard

- Status: Accepted (Nov 29, 2025)
- Deciders: Wordloom Core Team
- Context: Plan96/Plan104 regression fixes, ADR-093 (Chronicle timeline), ADR-094/ADR-096 (Bookshelf dashboard), DDD_RULES `POLICY-CHRONICLE-RECENT-EVENTS-V2` / `POLICY-BOOKSHELF-DASHBOARD-TIMEZONE-GUARD`
- Related Artifacts: frontend commit (ChronicleTimelineList stage regression labels), backend `GetBookshelfDashboardUseCase`, rules updates in HEXAGONAL_RULES & VISUAL_RULES (Nov 29, 2025)

## Problem

1. **Chronicle 近期事件缺口**：RECENT_EVENT_TYPES 仍只包含 stage changed 等旧类型，导致成熟度重算与结构任务事件无法进入 Book 工作区“最近事件”卡片。
2. **成熟度回退感知弱**：即使事件写入时间线，UI 标题始终显示“成熟度阶段变更”，回退信号被埋没，截图 1 中用户仍需手动比对 Stage Pill 才能发现回退。
3. **Dashboard 排序异常**：Bookshelf Dashboard 最近活动排序混用 offset-naive 与 timezone-aware datetime，触发 `TypeError: can't compare offset-naive and offset-aware datetimes` 并让书架统计区域抛出 500。

## Decision

1. **Chronicle Recent Events v2**
   - 扩展 RECENT_EVENT_TYPES 至 `BOOK_STAGE_CHANGED`、`BOOK_MATURITY_RECOMPUTED`、`STRUCTURE_TASK_COMPLETED`、`STRUCTURE_TASK_REGRESSED`，QueryService 默认应用该集合；Overview 卡片与 Timeline 列表共用同一过滤。
   - RecorderService 的 maturity/structure 事件 payload 统一包含 `previous_score`、`new_score`、`delta`、`stage`、`trigger`、`title`、`points`、`initial` 字段，保障 UI 能生成完整摘要。
   - ChronicleTimelineList 为这些事件新增中文标签与摘要模版，并根据阶段顺序自动输出“成熟度阶段晋级/回退”。

2. **Dashboard Timezone Guard**
   - 在 `GetBookshelfDashboardUseCase` 聚合 chronicle stats 时，将 `last_activity_at` 及 BookshelfModel 的 `created_at`/`updated_at` 全部转换为 `timezone.utc`，并在 DTO 中只返回 timezone-aware ISO 字符串。
   - 记录规则更新到 HEXAGONAL_RULES / DDD_RULES，保证未来拓展（例如 Library 级 dashboard）时沿用同一守卫。

## Consequences

- **正向**
  - 最近事件卡片与 Timeline 即时反映成熟度回退与结构任务得分，运营人员无需再翻查 Snapshot 或 Blocks。
  - Dashboard 不再抛出 TypeError，Pinned/Active 分区排序稳定，截图 1 中的统计卡可以正常加载。
  - 规则文件同步标记此次行为更改，阻止后续端口或 UI 回退到旧过滤。

- **负向**
  - RECENT_EVENT_TYPES 增加会让默认查询结果更长，如需继续限制数量需调小 limit 值。
  - Timezone 归一化对历史 Naive 数据执行 UTC 假设，若后续引入用户时区需要额外转换层。

## Implementation Notes

1. Backend
   - Update `chronicle/application/services.py` RECENT_EVENT_TYPES、payload assembly，以及 `GetBookshelfDashboardUseCase` datetime guard (`_ensure_timezone_aware`).
   - Add regression tests (manual for now) ensuring timezone guard prevents naive vs aware comparisons.
2. Frontend
   - Extend `ChronicleEventType` union, default filters, label/icon maps, and payload summarizer (`ChronicleTimelineList.tsx`).
   - Add stage order map to compute 晋级/回退标题；structure task events render ±points and stage badges.
3. Documentation & Governance
   - Sync HEXAGONAL_RULES/VISUAL_RULES/DDD_RULES with new policies.
   - Reference this ADR in future maturity or timeline changes to validate payload completeness and timezone handling.
