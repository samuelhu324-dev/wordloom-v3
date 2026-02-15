# ADR-001: Chronicle projection（chronicle_events → chronicle_entries）

Status: Adopted

## Context
Chronicle 需要一个可长期维护的 timeline 读模型：
- SoT（写模型）必须可追责、可回放：`chronicle_events`。
- 读模型需要可 rebuild、可演进：`chronicle_entries`。
- 读路径经常做时间排序+分页，而 `occurred_at` **不是唯一**，必须有稳定 tie-breaker。
- 投影需要可观测、可重试、可运维：复用 outbox/worker 的 lease/retry/failed/replay 能力。

核心约束（tenets）：

- SoT 优先：事件源是唯一真相，投影是可丢弃、可重建的产物。
- 可重建：任何时刻都应允许从 SoT 重建投影（用于纠错/回归/规则演进）。
- 可运营：失败必须可定位、可收敛、可重放且可审计（不是“靠重启碰运气”）。
- 分页稳定：统一用 `(occurred_at, id)` 做排序与游标，避免跳页/重复。

## Decision
采用「SoT + 可重建投影 + 可选 outbox 异步」的 Chronicle projection 方案：

- SoT：`chronicle_events` 作为唯一真相来源。
- Projection：`chronicle_entries` 为 timeline 的读模型，支持按规则 rebuild。
- 两条执行路径：
  - 同步重建（DB→DB）：`backend/scripts/rebuild_chronicle_entries.py --truncate`
  - outbox 路径（验证 worker/失败治理）：`--emit-outbox` + `backend/scripts/chronicle_outbox_worker.py`
- 稳定排序/分页：统一使用 `(occurred_at, id)` 作为排序与游标条件。
- 规则版本化：写入 `projection_version`（通过 `CHRONICLE_PROJECTION_VERSION` / `OUTBOX_PROJECTION_VERSION` 控制），允许对同一 SoT 重建不同版本产物。
- 失败治理：outbox 事件按 `pending/processing/done/failed` 状态机；
  - transient：安排重试（`pending + next_retry_at`），只有耗尽 `max_attempts` 才进入终态 `failed`
  - deterministic：直接终态 `failed`（低基数 `error_reason` + 可读的 `error`）
  - replay：`failed → pending` 必须由 ops 显式执行，并写入审计字段（`last_replayed_*`, `replay_count`）

## Alternatives considered

- 只做同步重建（不走 outbox）：
  - ✅ 实现简单；
  - ❌ 无法把“投影更新”与在线请求隔离，依赖抖动会直接影响写路径/用户体验。
- 只做异步 outbox（不提供 rebuild）：
  - ✅ 在线链路更轻；
  - ❌ 纠错成本高（坏数据/规则变更/历史补偿时缺少安全的全量重建入口）。
- 引入外部队列（Kafka/Redis streams）替代 DB outbox：
  - ✅ 更强的流式能力；
  - ❌ 依赖面与运维复杂度显著上升，不符合当前“先做最小闭环”的阶段目标。

## Consequences
- ✅ Chronicle timeline 读模型可 rebuild、可演进（规则变更可通过版本化和快照对照验证）。
- ✅ 分页稳定（避免 `occurred_at` 重复导致跳页/重复）。
- ✅ 运维闭环可复用（lease、retry/backoff、terminal failed、replay+audit）。
- ⚠️ 引入 outbox/worker 需要 runbook 与指标（lag、failed、oldest age、retry scheduled）。

## Links
- labs-005 操作指南与结论：`docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md`
- runbook（SOP）：`docs/architecture/runbook/run-003-chronicle-projection.md`
- labs 快照目录：`docs/architecture/runbook/labs/_snapshots/`
- outbox worker ADR（通用）：`docs/architecture/decisions/adr-003-outbox-daemon.md`
- Projections ADR（SoT vs Projection）：`docs/architecture/decisions/adr-001-projections.md`
- worker→daemon 演进 ADR：`docs/adr/adr-002-evolution-worker-to-daemon.md`

