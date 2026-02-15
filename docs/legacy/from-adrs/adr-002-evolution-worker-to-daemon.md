# ADR-002: Evolution — outbox worker → operable daemon (v1–v4)

Status: Adopted

## Context

项目在多个投影上使用 outbox worker（例如 Search：Postgres → Elasticsearch；Chronicle：DB → DB）。随着投影数量增加，运维成本会按比例上升：同样的“依赖抖动、处理卡死、失败终态、滚动重启”问题会在每个投影重复出现。

现状（v1–v3）已经具备 lease/reclaim、自适应重试、failed 终态与 replay 审计等语义，但缺少平台集成所需的 daemon 能力（可控 shutdown、显式 health/ready、运行时 guardrails 与告警口径），导致 worker 更像“脚本”而不是可长期运行的服务。

本 ADR 的目标是把 outbox worker 的能力分层固化为一套可复用的“worker→daemon”演进路线，并确保这套路线能跨投影复用（做第二个投影带来接近翻倍的收益）。

## Decision

按以下顺序演进 outbox worker（对应 v1–v4 能力分层），并将其作为所有投影 worker 的统一标准：

### v1 — Self-care / stuck handling

- 所有 worker 必须使用 lease/claim 语义避免并发竞争，支持水平扩容。
- 通过 lease 过期或 `max_processing_seconds` 识别 stuck，并周期性 reclaim 回到可重试状态。

### v2 — Failure containment / retry

- 将失败分类为 transient 与 deterministic：
  - transient：进入 `pending + next_retry_at`，使用 backoff+jitter 收敛，避免“自残式狂刷”。
  - deterministic：直接进入终态 `failed`，不做无限重试。
- 提供清晰、低基数的 `error_reason` 以便告警与聚合分析（error 字段保留可读上下文用于排障）。

### v3 — Catalog (DLQ) + replay (audited)

- failed 是终态（DLQ），必须可检索、可聚合、可统计（按 reason）。
- 提供显式 replay 工具：`failed → pending`，并写入审计字段（who/when/reason + replay_count）。
- runbook 必须定义最小 DB 快照与 replay 验收口径，避免“只靠日志猜测”。

### v4 — Operable / maintainable daemon

- graceful termination：处理 SIGTERM/SIGINT 时进入 draining，停止 claim 新任务，best-effort drain in-flight，并在 grace 超时后退出。
- platform integration：提供显式 `/healthz`（liveness）与 `/readyz`（readiness：是否安全接活）。
- runtime guardrails：依赖连续失败（至少 DB ping）达到阈值时进入 draining（`/readyz`=503，停止 claim），把故障从“扩大化”收敛为“可控等待/可运营处理”。
- alerts：告警以 metrics 为主（lag/oldest_age/stuck/retry/terminal_failed），阈值由 SLO/env 决定；guardrails 是进程内的最后一道“stop digging”安全网。

## Alternatives considered

- 继续把 worker 当脚本运行（没有 health/ready、只能靠重启）：
  - ✅ 最省改动；
  - ❌ 无法做滚动重启与稳定摘流，故障定位与恢复成本高。
- 用外部队列系统替代 DB outbox（Kafka/Redis streams）：
  - ✅ 更强的流式能力与生态；
  - ❌ 引入新的强依赖与运维面，不符合当前“先做最小闭环、跨投影复用”的阶段策略。
- 依赖平台 liveness（只做 health，不做 ready/guardrails）：
  - ✅ 实现简单；
  - ❌ 无法表达“依赖不健康时不要接活”，容易放大故障（重启风暴/抖动）。

## Consequences

- ✅ 同一套故障语义与运维口径可跨投影复用（新增投影的边际成本显著降低）。
- ✅ 失败从“不可控的异常日志”变为“可观测 + 可收敛 + 可重放”的运营对象。
- ✅ 支持安全滚动重启（SIGTERM draining + readiness 摘流）。
- ⚠️ 引入更多配置项（lease/backoff/grace/阈值），需要 runbook 明确默认值与调参风险。

## Links

- Log-S0B（v4：shutdown/health/ready/guardrails/alerts）：`docs/logs/logs/v2-logs/log-S0B-graceful-termination+heathz-readyz+alert-threshold.md`
- Labs-004（v1–v4）：`docs/architecture/runbook/labs/labs-004-worker-failure-management-v1-v4.md`
- Labs-006（Search 汇总 + v4 实验6）：`docs/architecture/runbook/labs/labs-006-search-projection-search-index-to-elastic.md`
- Labs-005（Chronicle；含 v4 实验6）：`docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md`
- Search runbook：`docs/architecture/runbook/run-002-search-projection.md`
- Chronicle runbook：`docs/architecture/runbook/run-003-chronicle-projection.md`
