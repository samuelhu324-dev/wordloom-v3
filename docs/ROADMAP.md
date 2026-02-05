# ROADMAP

## Current focus
Chronicle：Phase C 收口（server_default + 去重/TTL 策略 + 投影 runbook 对齐）

## Done
- Phase A：payload envelope 自动注入（correlation_id/source/actor_kind/…）
- Phase B：关键 facts 补齐（block/tag/book/todo/view/open 等）
- Phase C：envelope 升列 + 索引；server_default（暂不 NOT NULL）
- 高频写入治理：block_updated 多实例一致去重（DB 级）
- 前端修复：ChronicleTimelineList 缺失 icon import；global-tag-catalog queryFn 不返回 undefined

## Now（最多 5 条）
1. [Chronicle] Visit logs（book_viewed/book_opened）治理：DB 去重 + TTL/prune 策略落地 → [docs/chronicle/STATUS.md#v4](chronicle/STATUS.md#v4)
2. [Chronicle] Timeline 稳定排序与分页：ORDER BY occurred_at DESC, created_at DESC, id DESC（runbook 对齐）→ [docs/chronicle/STATUS.md#timeline-order](chronicle/STATUS.md#timeline-order)
3. [Chronicle] payload/index control 观测：提供“单 book 最近事件”统计 SQL + 指标口径 → [docs/chronicle/STATUS.md#payload-index-control](chronicle/STATUS.md#payload-index-control)
4. [Chronicle] Projection runbook（Labs-005）与当前实现保持一致并能复现 → [docs/chronicle/STATUS.md#runbook](chronicle/STATUS.md#runbook)
5. [Chronicle] ADR 补齐：envelope 升列、DB 去重窗口、visit TTL → [docs/chronicle/STATUS.md#adr](chronicle/STATUS.md#adr)

## Next（最多 10 条）
- [Chronicle] 将 visit logs 默认从主 Timeline 隐藏（仅“Show visit logs”展示）→ [docs/chronicle/STATUS.md#v4](chronicle/STATUS.md#v4)
- [Chronicle] 增加“写入路径覆盖率”观测（新列空值率趋势、按 source/actor_kind 分布）→ [docs/chronicle/STATUS.md#observability](chronicle/STATUS.md#observability)
- [Chronicle] 规划是否需要表分区（仅当写入量已证明不可控）→ [docs/chronicle/STATUS.md#partitioning](chronicle/STATUS.md#partitioning)
- [Chronicle] 统一命名：event_type 枚举 & Event Catalog 更新节奏 → [docs/chronicle/STATUS.md#catalog](chronicle/STATUS.md#catalog)
- [Chronicle] 历史数据 backfill 策略整理（只补可证明事实）→ [docs/chronicle/STATUS.md#backfill](chronicle/STATUS.md#backfill)

## Blocked / Risks（最多 5 条）
- 历史数据字段缺失：NOT NULL 暂缓；避免伪精确回填
- 高频事件索引过多会拖慢写入：谨慎加索引，优先治理事件量
- 多入口写入（api/worker/cron/backfill）覆盖不全会导致数据语义不一致

## Links
- Chronicle Event Catalog：[docs/architecture/modules/chronicle-projection.md](architecture/modules/chronicle-projection.md)
- Labs-005 runbook：[docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md](architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md)
- logs/others：[docs/logs/others/](logs/others/)