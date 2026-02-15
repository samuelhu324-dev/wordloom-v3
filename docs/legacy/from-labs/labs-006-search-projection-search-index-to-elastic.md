# Labs-006：Search 投影（search_index → elastic）小实验（操作指南 + 结论模板）

Status: adopted

目标：把 Search 投影补齐为“标准投影闭环”：

- SoT（稳定真相）：`search_index`（Postgres）
- Outbox（异步队列）：`search_outbox_events`
- 外部依赖：Elasticsearch
- 工程化能力：复用 outbox/worker 失败管理（lease/retry/failed/replay）+ v4 daemon 运行时工程化（SIGTERM、health/ready、guardrails）

完成后沉淀为 runbook：`docs/architecture/runbook/run-002-search-projection.md`

快照目录（证据留存）：`docs/architecture/runbook/labs/_snapshots/`

---

## 0) 前置条件

- Postgres（dev/test：localhost:5435）
- Elasticsearch（localhost:9200）
- 可选：Prometheus + Grafana

实现入口（与当前仓库对齐）：

- worker：`backend/scripts/search_outbox_worker.py`
- replay：`backend/scripts/search_outbox_replay_failed.py`
- v4 实验 runner：
  - `backend/scripts/ops_labs_004_v4_runtime_search_worker.sh`
  - `backend/scripts/ops_labs_004_v4_runtime_search_worker_capture.sh`

---

## 1) 实验映射（复用已有 labs）

为避免重复，本 labs 的实验 1–5 复用既有实验文档：

- 实验 1–3（观测与吞吐/lease）：
  - `docs/architecture/runbook/labs/labs-001-throughput-lagevents-observability.md`
  - `docs/architecture/runbook/labs/labs-002-bulk-observability.md`
  - `docs/architecture/runbook/labs/labs-003-lock-lease-observability.md`
- 实验 4–5（失败管理 v1–v3）：
  - `docs/architecture/runbook/labs/labs-004-worker-failure-management-v1-v4.md`（实验 1–5）

本文件只补齐 Search 的 **实验 6（v4）**：daemon 运行时工程化。

---

## 2) 实验 6（v4）：daemon 运行时工程化（graceful shutdown / health / readiness / guardrails）

目标：把 Search worker 从“脚本”升级为“可长期运维的 daemon”，验证最小闭环：

- SIGTERM：进入 draining，停止 claim 新任务，并在 `OUTBOX_SHUTDOWN_GRACE_SECONDS` 内退出
- `/healthz`：liveness（主循环在 tick）
- `/readyz`：readiness（可接活：未 draining + DB ok + （可选）ES ok）
- guardrails：DB 连续 ping 失败达到阈值后进入 draining（readyz=503，停止 claim）

### 2.1 参数建议（WSL2 / bash）

```bash
cd /mnt/d/Project/wordloom-v3

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-test-search-index'

export OUTBOX_WORKER_ID='w-v4'
export OUTBOX_METRICS_PORT=9109
export OUTBOX_HTTP_PORT=9111

export OUTBOX_SHUTDOWN_GRACE_SECONDS=10
export OUTBOX_DB_PING_FAILS_BEFORE_DRAINING=3

# 可选：强制 ES 作为 readiness gate
export OUTBOX_REQUIRE_ES_READY=1
```

### 2.2 一键验证（会自动落快照）

说明：runner 会把完整输出写入 `docs/architecture/runbook/labs/_snapshots/`。

```bash
bash backend/scripts/ops_labs_004_v4_runtime_search_worker_capture.sh
```

### 2.3 判定

- `/healthz`：200
- `/readyz`：依赖 OK 时 200；draining/DB 异常时 503
- SIGTERM：退出耗时 <= grace + 少量系统误差
- 判定：v4 daemon 工程化 `OK/FAIL`
