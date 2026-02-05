# Module: Search Projection

## SoT 是谁？

- SoT：Library/Bookshelf/Book/Block 等业务写模型（Postgres）。

## Scope key

- `library_id`（Phase 0 隔离仍以 Library owner 为准，但 Search 投影以 `library_id` 做范围过滤，为未来 tenant/workspace 演进留钩子）。

## 投影是什么？

- Postgres projection 表：`search_index`
  - 存放搜索文档（text/snippet/rank_score/event_version）
  - 包含 `library_id`
- Outbox：`search_outbox_events`
  - 描述对 ES 的 upsert/delete 事件

## 写路径（projection side）

- SoT 写入触发 domain event（例如 BookCreated/BlockUpdated…）
- handler/indexer 在同事务内：
  - upsert `search_index`
  - enqueue `search_outbox_events`

## 读路径

- API /search 从 Postgres projection 查询（feature flag 控制开关/回退）。

## 一致性与 SLO（建议）

- API：GET /search 关注 P95/P99（读快不快）
- worker：关注 outbox lag / oldest age / failed rate（投影新不新）

## 观测入口

- Grafana dashboard: “Wordloom • Outbox + ES Bulk”
- Prometheus scrape 目标：见 docker/prometheus/prometheus.yml
