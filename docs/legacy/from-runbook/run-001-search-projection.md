# Run-002：Search 投影（search_index → elastic）SOP

对应实验（操作与结论）：

- labs（失败治理 v1–v4）：`docs/architecture/runbook/labs/labs-004-worker-failure-management-v1-v4.md`
- labs（Search 投影汇总 + v4 实验6）：`docs/architecture/runbook/labs/labs-006-search-projection-search-index-to-elastic.md`
- 快照目录（证据留存）：`docs/architecture/runbook/labs/_snapshots/`
- ADR（worker→daemon 分层决策）：`docs/adr/adr-002-evolution-worker-to-daemon.md`

---

## 1) 目的与范围

- 目标：把 Search 投影做成可长期运维的闭环（可 rebuild、可观测、失败可运营、可滚动重启）。
- 范围：`search_index_to_elastic` 投影 outbox worker（Postgres → Elasticsearch）。
- 不在范围：ES mapping 设计与业务一致性规则（属于 Search domain / 索引策略）。

---

## 2) 关键定义（口径统一）

- **SoT（Source of Truth）**：`search_index`（Postgres），表示“可重建的索引真相”。
- **Outbox**：`search_outbox_events`，异步队列（pending/processing/done/failed）。
- **Projection**：Elasticsearch index（例如 `wordloom-test-search-index`）。
- **pending**：等待处理；可能有 `next_retry_at`。
- **processing**：已被某 worker claim；应当带 lease / processing_started_at。
- **failed（终态）**：不会自动复活；只能通过显式 replay 回到 pending，并写审计字段。
- **stuck**：processing 且 lease 过期或处理超时（max_processing_seconds）。

---

## 3) 依赖与前置条件

- Postgres（dev/test）：localhost:5435（dev/test DB 名隔离）
- Elasticsearch：localhost:9200
- API（产生 outbox）
- Search outbox worker：`backend/scripts/search_outbox_worker.py`
- Prometheus + Grafana（可选但推荐）：`docker-compose.infra.yml` 的 monitoring profile

参考：`docs/ENVIRONMENTS.md`

---

## 4) 启动与停止

### 4.1 启动顺序（dev/test）

1) 起 DB（devtest-db-5435）
2) 起 ES（infra-only compose）
3) 起 API（暴露 /metrics）
4) 起 worker（/metrics + v4: /healthz,/readyz）

### 4.2 worker 启动（示例：WSL2/Bash，test）

```bash
cd /mnt/d/Project/wordloom-v3

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-test-search-index'

export OUTBOX_WORKER_ID='w1'
export OUTBOX_METRICS_PORT=9109

# v4 runtime endpoints
export OUTBOX_HTTP_PORT=9111

python3 backend/scripts/search_outbox_worker.py
```

### 4.3 停止（v4：建议 SIGTERM）

说明：v4 支持 SIGTERM draining（停止 claim 新任务）+ grace 超时退出。

---

## 4.4 快速自检（最少 60 秒把系统“摸清楚”）

- runtime endpoints（v4）：
  - `/healthz`：主循环是否在 tick（liveness）
  - `/readyz`：是否“可接活”（readiness：未 draining + DB ok +（可选）ES ok）
- `/metrics`：用于告警与趋势观测（lag/oldest_age/retry/failed）

最小命令（WSL2/Bash 示例）：

```bash
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9111}/healthz" | cat; echo
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9111}/readyz"  | cat; echo
curl -fsS "http://localhost:${OUTBOX_METRICS_PORT:-9109}/metrics" | egrep '^outbox_(lag_events|oldest_age_seconds|inflight_events|processed_total|failed_total|stuck_processing_events|retry_scheduled_total|terminal_failed_total)' || true
```

---

## 5) Migration

- dev：运行 guarded 脚本升级到 head
- test：同上

说明：脚本会强制校验 host/port/dbname，避免连错库。

---

## 6) Rebuild

- 从 SoT 全量重建 Postgres projection：
  - `python backend/scripts/rebuild_search_index.py --truncate`
- 如果需要同步 ES：
  - `python backend/scripts/rebuild_search_index.py --truncate --emit-outbox`
  - 然后启动 worker 消费 outbox

---

## 7) Feature flag（读路径开关）

- `ENABLE_SEARCH_PROJECTION`（或 settings 对应 env）
  - off：读路径返回空（快速回退）
  - on：读路径走 projection

---

## 8) 观测与告警

### 8.1 必看指标（worker）

- lag：`outbox_lag_events{component="worker"}`
- oldest age：`outbox_oldest_age_seconds{component="worker"}`
- inflight：`outbox_inflight_events{component="worker"}`
- retry：`outbox_retry_scheduled_total{component="worker"}`
- terminal failed：`outbox_terminal_failed_total{component="worker"}`（按 error_reason 聚合）

### 8.2 DB 快照查询（最准确）

```sql
-- 1) 状态分布
select status, count(*) as n
from search_outbox_events
group by status
order by n desc;

-- 2) 终态 failed 的 Top 原因
select coalesce(error_reason, '(null)') as error_reason, count(*) as n
from search_outbox_events
where status = 'failed'
group by 1
order by n desc
limit 20;

-- 3) 最近 24h 是否持续产生终态 failed
select count(*) as failed_24h
from search_outbox_events
where status = 'failed'
  and updated_at > now() - interval '24 hours';

-- 4) pending backlog 与最老年龄（秒）
select
  count(*) as pending,
  coalesce(extract(epoch from (now() - min(created_at))), 0)::bigint as oldest_age_s
from search_outbox_events
where status = 'pending'
  and processed_at is null;

-- 5) 抽样查看 failed
select entity_type, op, attempts, updated_at, error_reason, left(coalesce(error,''), 300) as error_snip
from search_outbox_events
where status = 'failed'
order by updated_at desc
limit 50;
```

### 8.3 推荐告警（起步口径）

说明：具体阈值依赖 env/SLO；建议先从“oldest_age + terminal_failed + stuck”三件套开始，并结合趋势调参。

- oldest_age 超过 SLA（例如 warning 5m / critical 30m）
- terminal_failed_total 突增（按 error_reason 聚合定位）
- stuck_processing_events > 0 且持续 N 分钟

---

## 9) 失败终态与 replay（可审计）

> 注意：failed 是终态，不会自动复活。

replay 脚本：`backend/scripts/search_outbox_replay_failed.py`

- dry-run：`python backend/scripts/search_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100 --dry-run`
- 执行：`python backend/scripts/search_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100`

审计要求：

- who/when/reason 必须写入
- `replay_count` 递增

---

## 10) 实验 6（v4）：daemon 运行时工程化（graceful shutdown / health / readiness / guardrails）

本节是“运维闭环”的最小验收入口。详细步骤与快照规范见：

- `docs/architecture/runbook/labs/labs-006-search-projection-search-index-to-elastic.md`（实验 6）
- `docs/architecture/runbook/labs/labs-004-worker-failure-management-v1-v4.md`（实验 6）

一键验证（会自动落快照）：

```bash
bash backend/scripts/ops_labs_004_v4_runtime_search_worker_capture.sh
```

---

## 11) 常见故障处理（SOP）

### 11.1 ES 不可用 / 429 / 5xx（transient）

- 预期行为：进入 retry/backoff（`pending + next_retry_at`），`/readyz` 是否 gate ES 取决于 `OUTBOX_REQUIRE_ES_READY`。
- 操作：
  - 先确认依赖：ES 是否可达、是否限流
  - 看指标：`retry_scheduled_total`、`oldest_age_seconds` 是否持续上升
  - 必要时降吞吐：降低批量/并发，观察失败率与 oldest_age 是否回落

### 11.2 确定性错误（mapping 冲突 / 坏 payload）

- 预期行为：进入终态 `failed`（可审计），不会无限重试。
- 操作：按 `error_reason` 聚合定位根因，修复后 replay。

### 11.3 stuck（processing 长时间不动）

- 预期行为：lease/max_processing 到期后 reclaim 自愈。
- 操作：看 `stuck_processing_events` 与 reclaim 日志/指标是否回落；必要时检查 lease/max_processing 配置是否合理。

---

## 12) 回归验证

- 失败治理回归：跑一遍 labs-004（v1–v4）
- Search 投影回归：跑一遍 labs-006（实验映射 + v4 实验6）


