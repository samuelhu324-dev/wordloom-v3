# Log-001: DLQ + replay as a platform (search + chronicle)
<!-- Log-001：将 DLQ + replay 作为平台能力（Search + Chronicle） -->

Status: adopted
<!-- 状态：草稿 -->

links: [backend/scripts/search_outbox_worker.py](../../../../backend/scripts/search_outbox_worker.py), [backend/scripts/chronicle_outbox_worker.py](../../../../backend/scripts/chronicle_outbox_worker.py), [backend/scripts/search_outbox_replay_failed.py](../../../../backend/scripts/search_outbox_replay_failed.py), [backend/scripts/chronicle_outbox_replay_failed.py](../../../../backend/scripts/chronicle_outbox_replay_failed.py)
<!-- 链接：Search/Chronicle 两个 projection 的 worker 与 replay 脚本（用于双重核对与后续落地）。 -->

## Background
DLQ + replay is a **fixed-cost platform capability**: you pay most of the engineering/ops cost once, but the payoff grows roughly linearly as more projections use it. With only one projection, it can feel overbuilt; with **two or more projections** (already: search + chronicle), it becomes infrastructure: shared failure model, shared ops workflows, shared SLOs, plus “control group” diagnosis.
<!-- DLQ + replay 是一种**固定成本的平台能力**：工程/运维的大部分投入只需要做一遍，但随着挂载的 projection 增多，收益会近似线性增长。只有 1 个 projection 时会显得“过度建设”；当 projection ≥ 2（已具备：search + chronicle）时，它会变成基础设施：共享失败模型、共享运维操作、共享 SLO，并且还能通过“对照组”提升诊断效率。 -->

## What/How to do
<!-- 怎么做 / 怎么推进 -->

### 1) Standardize the DLQ contract across projections
<!-- 1）标准化跨 projection 的 DLQ 合同（字段/状态/语义统一） -->

draft:
- Align the outbox lifecycle and fields between `search_outbox_events` and `chronicle_outbox_events`: `pending/processing/done/failed`, `attempts`, `next_retry_at`, `error_reason`, `error`, `owner`, `lease_until`, `processing_started_at`, replay audit fields.
  <!-- 对齐 `search_outbox_events` 与 `chronicle_outbox_events` 的生命周期与字段：`pending/processing/done/failed`、`attempts`、`next_retry_at`、`error_reason`、`error`、`owner`、`lease_until`、`processing_started_at`，以及 replay 审计字段。 -->
- Normalize failure taxonomy to **low-cardinality** `error_reason` values shared by both workers (e.g., `http_429`, `http_5xx`, `http_4xx`, `timeout`, `connect`, `deterministic_exception`, `unknown_exception`, `es_4xx/es_5xx/es_429`).
  <!-- 统一失败分类为**低基数**的 `error_reason`（两套 worker 共享），例如 `http_429`、`http_5xx`、`http_4xx`、`timeout`、`connect`、`deterministic_exception`、`unknown_exception`、`es_4xx/es_5xx/es_429`。 -->
- Standardize retry policy knobs and defaults across projections (`MAX_ATTEMPTS`, backoff+jitter, `MAX_PROCESSING_SECONDS` cap), so operators don’t need to relearn per projection.
  <!-- 统一重试策略的开关与默认值（`MAX_ATTEMPTS`、指数退避+抖动、`MAX_PROCESSING_SECONDS` 上限），让运维不必每个 projection 重新学习一套规则。 -->

adopted:

- Align the DB contract across projections (search + chronicle): `pending/processing/done/failed`, `attempts`, `next_retry_at`, `owner`, `lease_until`, `processing_started_at`, `error_reason`, `error`, plus replay audit fields.
- Keep `error_reason` low-cardinality and shared where possible (e.g., `deterministic_exception`, `unknown_exception`, and projection-specific families like `es_429/es_5xx`).
- Standardize worker knobs and defaults (max attempts, backoff+jitter, reclaim/stuck scans, processing time caps) so operators don’t need per-projection relearning.


### 2) Make replay operations a single mental model
<!-- 2）让 replay 成为“单一心智模型”（同一套操作习惯） -->

draft:
- Keep per-projection replay scripts, but enforce the **same CLI shape** and audit fields (`--by`, `--reason`, `--limit`, `--entity-type`, `--since-hours`, `--dry-run`) so replay is muscle memory.
  <!-- 保留每个 projection 各自的 replay 脚本，但强制 **CLI 形状一致**与审计字段一致（`--by`、`--reason`、`--limit`、`--entity-type`、`--since-hours`、`--dry-run`），形成肌肉记忆。 -->
- Define safe operator actions as a checklist: `replay` / `drop` / `requeue with patch` / throttle (bulk size, concurrency) / disable a read-path feature flag (if applicable).
  <!-- 把“安全的人为介入动作”写成 checklist：`replay` / `drop` / `requeue with patch` / 限流（bulk size, concurrency）/ 关闭读路径 feature flag（如果存在）。 -->
- Add “DB snapshot queries” to both runbooks: status distribution, oldest pending/failed, stuck scan, top `error_reason` by count.
  <!-- 在两套 runbook 里补上“DB 快照查询”：状态分布、最老 pending/failed、stuck 扫描、按数量统计 Top `error_reason`。 -->

adopted:

- Keep per-projection replay scripts, but enforce a consistent operator interface and audit fields: `--by`, `--reason`, `--dry-run`, bounded scope (`--limit` and/or targeted selectors like `--ids`).
- Treat `failed` as terminal: workers do not auto-retry `failed`; ops must explicitly replay to `pending` after a fix.
- Document a safe ops checklist: snapshot DB → classify error_reason → apply fix/mitigation → replay (scoped) → confirm convergence (done) → record evidence snapshot.
- Ensure runbooks include standard snapshot queries: status distribution, oldest pending/failed, stuck scan, top `error_reason` counts.


### 3) Operate with system-level SLOs (not per-projection ad-hoc)
<!-- 3）用系统级 SLO 运维（避免每个 projection 各玩各的） -->

draft:
- Define a shared metrics view across projections using the existing `projection` label: lag, oldest age, inflight, stuck, failed rate, terminal failed rate, retry scheduled rate.
  <!-- 基于现有的 `projection` label，建立跨 projection 的统一指标视图：lag、oldest age、inflight、stuck、失败率、终态失败率、安排重试率。 -->
- Add a DLQ-centric dashboard slice: “new failed per hour”, “terminal failed per hour”, “retry success rate (approx)”, and “oldest_age not decreasing”.
  <!-- 补一个以 DLQ 为中心的 dashboard 切片：每小时新增 failed、每小时新增终态 failed、重试成功率（近似）、以及 “oldest_age 不下降”。 -->
- Set alert thresholds that are projection-agnostic first, then allow projection-specific overrides (avoid bespoke tuning too early).
  <!-- 先设置 projection 无关的通用告警阈值，再允许少量 projection 特例（避免过早定制化导致维护成本飙升）。 -->

adopted:

- Operate DLQ/replay with shared SLO vocabulary across projections: lag, oldest age, inflight, stuck, failed rate, terminal failed rate, retry scheduled rate.
- Export/visualize metrics with a `projection` label to enable one dashboard slice for all projections, then allow minimal projection-specific overrides.
- Alert on system-level symptoms first (oldest_age not decreasing, terminal failed increasing), then tune thresholds per projection only when needed.


### 4) Use multi-projection as a diagnostic control group
<!-- 4）用多投影做“对照组”诊断（定位快一个量级） -->

draft:
- Adopt the diagnosis rule of thumb:
  <!-- 采用一个简单但很有效的诊断经验法则： -->
  - both projections failing ⇒ producer/outbox/DB/environment issue;
    <!-- 两个都失败 ⇒ 生产侧 / outbox / DB / 环境级问题。 -->
  - only search failing ⇒ ES/mapping/network/backpressure;
    <!-- 只有 search 失败 ⇒ ES / mapping / 网络 / 背压（429）等外部依赖问题。 -->
  - only chronicle failing ⇒ projector/schema/semantic invariants.
    <!-- 只有 chronicle 失败 ⇒ projector / schema 变更 / 事件语义约束（不变式）问题。 -->
- Ensure `correlation_id` is consistently available where it matters (envelope/outbox payload/columns), so ops can drill down “one request fan-out” across projections.
  <!-- 确保 `correlation_id` 在关键位置一致可用（envelope / outbox payload / 列字段），让运维可以按“一次请求扇出”跨 projection 追踪。 -->
- Decide DLQ retention/prune policy that matches each projection’s nature (search: external dependency spikes; chronicle: audit semantics + future TTL/archiving work).
  <!-- 制定与 projection 性质匹配的 DLQ 保留/清理策略（search：外部依赖短暂不可用；chronicle：审计语义 + 未来 TTL/归档工作）。 -->

adopted:

- Use “control group” diagnosis:
  - both projections failing ⇒ producer/outbox/DB/environment issue
  - only search failing ⇒ ES/network/backpressure
  - only chronicle failing ⇒ projector/schema/semantic invariants
- Prefer `correlation_id` (envelope/columns) as the cross-projection drill-down key when available.
- Define retention/prune policy per projection, but keep the operational workflow (snapshot → classify → replay → verify) identical.

