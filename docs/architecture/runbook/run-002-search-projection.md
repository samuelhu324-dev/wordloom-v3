# Runbook: Search Projection

这份运行手册覆盖：如何跑、如何重建、如何开关、如何排障。

## 1. 依赖服务

- Postgres（dev/test）：localhost:5435（dev/test DB 名隔离）
- Elasticsearch：localhost:9200
- Prometheus/Grafana（可选但推荐）：docker-compose.infra.yml 的 monitoring profile

## 2. 启动顺序（dev/test）

1) 起 DB（devtest-db-5435）
2) 起 ES（infra-only compose）
3) 起 API（暴露 /metrics）
4) 起 worker（暴露 /metrics，默认 9108；test 常用 9109）

## 3. Migration

- dev：运行 guarded 脚本升级到 head
- test：同上

（脚本会强制校验 host/port/dbname，避免连错库）

## 4. Rebuild

- 从 SoT 全量重建 Postgres projection：
  - `python backend/scripts/rebuild_search_index.py --truncate`
- 如果需要同步 ES：
  - `python backend/scripts/rebuild_search_index.py --truncate --emit-outbox`
  - 然后启动 worker 消费 outbox

## 5. Feature flag（读路径开关）

- `ENABLE_SEARCH_PROJECTION`（或 settings 对应 env）
  - off：读路径返回空（快速回退）
  - on：读路径走 projection

## 6. Prometheus / Grafana 指标（关键）

### 6.1 读快不快（API：P95/P99）

- 交互型 API：
  - 例：GET /search：P95 < 2s，P99 < 10s

（具体请求耗时指标取决于 API 侧 instrumentation；如果当前还没打 request duration metrics，可以后续补 FastAPI middleware。）

### 6.2 投影新不新（worker）

建议关注这三类：

- lag：`outbox_lag_events{component="worker"}`
- oldest age：`outbox_oldest_age_seconds{component="worker"}`
- error rate：`rate(outbox_failed_total{component="worker"}[1m])`

以及吞吐：

- produced：`rate(outbox_produced_total{component="api"}[1m])`
- processed：`rate(outbox_processed_total{component="worker"}[1m])`

### 6.3 Rebuild 运行情况（运维）

- 上次 rebuild 耗时（秒）：`projection_rebuild_duration_seconds{component="worker"}`
- 上次 rebuild 完成时间（unix timestamp）：`projection_rebuild_last_finished_timestamp_seconds{component="worker"}`
- 上次 rebuild 是否成功（1/0）：`projection_rebuild_last_success{component="worker"}`

### 6.4 library 维度拆分（建议）

- 第一版不直接按 `library_id` 打 label（避免 Prometheus 高基数）。
- 如需拆分：优先用 `library_bucket = hash(library_id) % 64` 之类的分桶，或 Top-N 单独追踪。

## 7. 常见排障

- lag 持续上涨：
  - 看 processed / produced 是否长期倒挂
  - 看 outbox_failed_total 是否持续增加（mapping/429/5xx）
- oldest age 很大但 lag 不大：
  - 通常是有 stuck 的 failed row（需要人工处理/修复后重放）
- ES 不可用/429：
  - 先降吞吐（OUTBOX_BULK_SIZE/CONCURRENCY）
  - 或启用 backoff 观察失败率是否下降
