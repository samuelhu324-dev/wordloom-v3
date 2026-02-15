# Run-003：Chronicle 投影（chronicle_events → chronicle_entries）SOP

对应实验（操作与结论）：

- labs：`docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md`
- 快照目录（证据留存）：`docs/architecture/runbook/labs/_snapshots/`
- ADR（精炼决策）：`docs/adr/adr-001-chronicle-projection-chronicle-events-to-entries.md`
- ADR（worker→daemon 分层决策）：`docs/adr/adr-002-evolution-worker-to-daemon.md`

---

## 1) 目的与范围

- 目标：把 Chronicle 做成第二个标准投影闭环：SoT（chronicle_events）稳定、投影（chronicle_entries）可重建、失败可运营。
- 范围：chronicle 读优化投影（DB→DB），并复用 outbox/worker 的失败管理（v1–v3）+ v4 运行时工程化（daemon）。
- 不在范围：前端展示规则细节（UI 文案/排版），以及业务授权模型本身（由 Chronicle domain/application 负责）。

---

## 2) 关键定义（口径统一）

- **SoT（Source of Truth）**：`chronicle_events`，表示“发生过的动作/事件”，携带动作上下文。
- **投影（Projection）**：`chronicle_entries`（或 chronicle_event_summaries），面向 UI/筛选/全文/聚合 的读模型。
- **动作上下文（Action Context）**：让一条事件具备“可读性 + 可追责性 + 可复盘性”的信息集合（见 3）。
- **幂等键**：建议 `chronicle_entries.id = chronicle_event_id`，确保重放/rebuild 不产生重复。

---

## 3) 动作上下文（推荐模板）

> 目标：确保 `chronicle_events` 是“可回放的真相胶片”。

建议每条事件至少具备：

- 谁做的：`actor_user_id`（或 actor / owner）
- 对哪个对象：`entity_type` + `entity_id`（book / block / tag…）
- 做了什么：`event_type`（BookRenamed / BlockUpdated / TagAdded…）
- 从什么变成什么：`before`/`after`（或 `diff`）
- 何时：`occurred_at`（业务时间）+ `created_at`（写入时间）
- 在哪/通过什么（可选）：`request_id`、`device/client`、`ip`
- 为什么/附注（可选）：`reason/comment`

运行口径：

- 事件写入必须遵守授权/隔离（scope：如 library_id / user_id）。
- 事件必须可排序且可分页稳定（建议 (occurred_at, id) 游标）。

---

## 4) 依赖与前置条件

- Postgres（dev/test）
- API（写入 chronicle_events；或脚本注入事件）
- Chronicle projector worker（消费 chronicle_outbox_events，写入 chronicle_entries）
- Prometheus + Grafana（可选但推荐）

参考：`docs/ENVIRONMENTS.md`

---

## 5) 运行形态（建议：方案 A）

> 先做独立 outbox 表，降低改动面与风险。

- SoT：`chronicle_events`
- Outbox：`chronicle_outbox_events`（独立表；字段建议与 search_outbox_events 同构）
- 投影结果：`chronicle_entries`
- Worker：`backend/scripts/chronicle_outbox_worker.py`
- Replay：`backend/scripts/chronicle_outbox_replay_failed.py`
- Rebuild：`backend/scripts/rebuild_chronicle_entries.py`

---

## 6) 启动与停止

本 SOP 的默认目标环境：`wordloom_test`（devtest-db:5435）。

说明：为了“可重复 + 可留证据”，推荐用 labs-005 runner 脚本执行，并自动输出快照到 `docs/architecture/runbook/labs/_snapshots/`。

### 6.1 启动顺序

1) DB
2) API
3) projector worker
4) Prom/Grafana（可选）

### 6.2 PowerShell（Windows / devtest-db:5435，推荐）

```powershell
cd d:\Project\wordloom-v3

./backend/scripts/ops/devtest_db_5435_start.ps1
./backend/scripts/ops/devtest_db_5435_migrate.ps1 -Database wordloom_test

$env:DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
$env:OUTBOX_WORKER_ID='c1'
$env:OUTBOX_METRICS_PORT='9110'

# v4 runtime endpoints
$env:OUTBOX_HTTP_PORT='9112'
$env:OUTBOX_SHUTDOWN_GRACE_SECONDS='10'
$env:OUTBOX_DB_PING_FAILS_BEFORE_DRAINING='3'

python backend/scripts/chronicle_outbox_worker.py
```

### 6.3 WSL2/Bash（一键 runner，推荐用于留证据快照）

```bash
cd /mnt/d/Project/wordloom-v3

./backend/scripts/ops_labs_005_chronicle.sh .env.test sync
./backend/scripts/ops_labs_005_chronicle.sh .env.test outbox 20
```

---

## 6.4 快速自检（最少 60 秒把系统“摸清楚”）

- runtime endpoints（v4）：
  - `/healthz`：主循环是否在 tick（liveness）
  - `/readyz`：是否“可接活”（readiness：未 draining + DB ok）
- `/metrics`：用于告警与趋势观测（lag/oldest_age/retry/failed）

最小命令（端口以你的 env 为准）：

```bash
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9112}/healthz" | cat; echo
curl -fsS "http://localhost:${OUTBOX_HTTP_PORT:-9112}/readyz"  | cat; echo
curl -fsS "http://localhost:${OUTBOX_METRICS_PORT:-9110}/metrics" | egrep '^outbox_(lag_events|oldest_age_seconds|inflight_events|processed_total|failed_total|stuck_processing_events|retry_scheduled_total|terminal_failed_total)' || true
```

---

## 7) Rebuild（读模型可重建）

- 目标：从 `chronicle_events` 全量重建 `chronicle_entries`。

推荐（带快照留存）：

- 同步重建（DB→DB）+ 快照：
  - `./backend/scripts/ops_labs_005_chronicle.sh .env.test sync`
- outbox 路径（验证 worker/失败治理）+ 快照：
  - `./backend/scripts/ops_labs_005_chronicle.sh .env.test outbox 20`

直连脚本（不自动落快照，适合调试）：

- 直接写 entries（同步重建）：`python backend/scripts/rebuild_chronicle_entries.py --truncate`
- 走 outbox：`python backend/scripts/rebuild_chronicle_entries.py --truncate --emit-outbox`

---

## 8) 观测与告警

### 8.1 必看指标

- outbox：lag / oldest_age / inflight
- retry：retry_scheduled_total
- terminal failed：terminal_failed_total（按 error_reason 维度聚合）

最小 DB 快照查询（无需 metrics 也能排障）：

- outbox 状态分布：`select status, count(*) from chronicle_outbox_events group by 1 order by 1;`
- 最老 pending：`select id, created_at, next_retry_at, attempts, error_reason from chronicle_outbox_events where status='pending' order by coalesce(next_retry_at, created_at) asc limit 20;`
- 最近 failed：`select id, updated_at, attempts, error_reason, left(error, 120) from chronicle_outbox_events where status='failed' order by updated_at desc limit 20;`

### 8.2 推荐告警（占位）

- oldest_age 超过 SLA
- terminal_failed_total 突增（按 error_reason 定位）
- stuck_processing_events > 0 且持续 N 分钟（如启用 lease/reclaim）

---

## 9) 常见故障处理（SOP）

### 9.1 DB 不可用 / 网络抖动

- 预期行为：DB ping 连续失败达到阈值后进入 draining（`/readyz`=503，停止 claim）。
- 操作：
  - 先恢复 DB 连通性
  - 再观察 `/readyz` 是否恢复 200，lag 是否开始回落

### 9.2 deterministic 错误（坏数据/不变式）

- 预期行为：进入终态 `failed`，写入 `error_reason + error`，需要显式 replay。
- 操作：按 `error_reason` 聚合定位根因，修复后 replay。

---

## 10) v4 daemon 运行时工程化（实验 6）

Chronicle 的 v4 验收入口在 labs-005 的实验 6：

- `docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md`（实验 6）
- 一键验证（会自动落快照）：`bash backend/scripts/ops_labs_005_chronicle_e6_runtime_worker_capture.sh`

---

## 11) 失败终态与 replay（可审计）

replay 脚本：`backend/scripts/chronicle_outbox_replay_failed.py`

安全操作建议：先 dry-run，再执行；优先限定范围（limit/ids）。

- dry-run：`python backend/scripts/chronicle_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100 --dry-run`
- 执行：`python backend/scripts/chronicle_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100`
- 精确重放（推荐）：`python backend/scripts/chronicle_outbox_replay_failed.py --by ops --reason "fix applied" --ids <outbox_id_1> <outbox_id_2>`

最小验收：

- replay 之后：failed 的行变成 pending
- `replay_count + 1`
- `last_replayed_at/last_replayed_by/last_replayed_reason` 写入

---

## 12) 回归验证

- 回归入口：跑一遍 labs-005（会把证据输出到 `docs/architecture/runbook/labs/_snapshots/`）：
  - `./backend/scripts/ops_labs_005_chronicle.sh .env.test sync`
  - `./backend/scripts/ops_labs_005_chronicle.sh .env.test outbox 20`
  - `./backend/scripts/ops_labs_005_chronicle_e4_pagination.sh .env.test`
  - `./backend/scripts/ops_labs_005_chronicle_e5_failure.sh .env.test`
  - `bash backend/scripts/ops_labs_005_chronicle_e6_runtime_worker_capture.sh`

