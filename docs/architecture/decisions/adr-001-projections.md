# ADR-001: Projections (SoT vs Projection)

## Context

- 需要把读性能/检索能力从 SoT 写模型中解耦。
- Search 属于典型投影：可 eventual consistency、可 rebuild。

## Decision

- SoT 写入后，同事务写入 Postgres projection（`search_index`）并 enqueue outbox（`search_outbox_events`）。
- Outbox worker 异步把投影同步到 Elasticsearch。
- 读路径由 feature flag 控制，可灰度/回退。

## Consequences

- 写路径更可靠（outbox 在同事务里），读路径可扩容。
- 需要运维能力：rebuild、监控 lag、排障流程。
