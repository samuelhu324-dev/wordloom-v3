# ADR-003: Outbox worker (daemon)

## Context

- 需要把投影更新从 API 请求生命周期中分离。
- 必须可观测（throughput、lag、失败率）且可重试。

## Decision

- 使用 outbox 表 + worker 轮询消费。
- worker 通过 lease/claim 避免并发竞争（支持扩容）。
- Prometheus metrics 导出：produced / processed / failed / lag。

## Consequences

- 投影具备最终一致性。
- 需要 runbook：重建、重试、处理失败事件。
