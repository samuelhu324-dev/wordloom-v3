# ADR-002: Chronicle 高频事件用 DB 窗口去重（多实例一致）

Status: Adopted

## Context
高频事件（尤其编辑器类过程事件）会导致：
- chronicle_events 写入量线性膨胀
- 多实例下内存节流不一致（每个实例都写一份）

## Decision
对指定高频事件（先从 `block_updated` 开始）使用 Postgres 原子写入实现“多实例一致抽稀”。
- 维护去重状态表（key: event_type + book_id + block_id + actor_id + window_seconds）
- 通过条件 upsert/更新推进 bucket；只有推进成功的请求才允许写入 chronicle_events/outbox

## Consequences
- ✅ 多实例一致（唯一胜出写入）
- ✅ 控制事件量上限（按窗口）
- ⚠️ 需要谨慎选择 key 粒度，避免误抑制（尤其 actor_id/correlation_id 的取舍）

## Links
- docs/chronicle/STATUS.md#v4
- docs/logs/others/others-047-source-of-truth-projection-chronicle-7.md
