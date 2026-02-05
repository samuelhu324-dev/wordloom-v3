# Run-004：Chronicle 投影（chronicle_events → chronicle_entries）（模板 / 待填充）

> 说明：本 runbook 是“模板占位”。
> 等 labs-005 跑通并写出结论后，再把本文件从“模板”升级为“可执行 SOP”。
>
> 对应实验：`docs/architecture/runbook/labs/labs-005-chronicle-projection-chronicle-events-to-entries.md`

---

## 1) 目的与范围

- 目标：把 Chronicle 做成第二个标准投影闭环：SoT（chronicle_events）稳定、投影（chronicle_entries）可重建、失败可运营。
- 范围：chronicle 读优化投影（DB→DB），并复用 outbox/worker 的失败管理（v1–v3）。
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

## 6) 启动与停止（TODO：实现后补齐）

### 6.1 启动顺序

1) DB
2) API
3) projector worker
4) Prom/Grafana（可选）

### 6.2 启动命令（占位）

#### 6.2.1 PowerShell（Windows / devtest-db:5435，推荐）

```powershell
cd d:\Project\wordloom-v3

# 1) 启动 devtest DB（5435）
./backend/scripts/devtest_db_5435_start.ps1

# 2) 跑迁移（test）
./backend/scripts/devtest_db_5435_migrate.ps1 -Database wordloom_test

# 3) 启动 worker（可选：OUTBOX_RUN_SECONDS 做一次性 smoke run）
$env:DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
$env:OUTBOX_WORKER_ID='c1'
$env:OUTBOX_METRICS_PORT='9110'
$env:OUTBOX_BATCH_SIZE='50'
$env:OUTBOX_POLL_INTERVAL_SECONDS='0.2'
$env:OUTBOX_LEASE_SECONDS='30'
$env:OUTBOX_MAX_ATTEMPTS='10'
$env:OUTBOX_BASE_BACKOFF_SECONDS='0.5'
$env:OUTBOX_MAX_BACKOFF_SECONDS='30'
$env:OUTBOX_RECLAIM_INTERVAL_SECONDS='5'
$env:OUTBOX_MAX_PROCESSING_SECONDS='600'

# smoke：跑 2 秒后退出；生产/常驻运行时不要设置这个
$env:OUTBOX_RUN_SECONDS='2'

python backend/scripts/chronicle_outbox_worker.py

# 4) 最小验收（容器名通常是：wordloom-devtest-db_devtest-1）
docker exec wordloom-devtest-db_devtest-1 psql -U wordloom -d wordloom_test -c "select status, count(*) from chronicle_outbox_events group by 1 order by 1;"
docker exec wordloom-devtest-db_devtest-1 psql -U wordloom -d wordloom_test -c "select count(*) from chronicle_entries;"
```

- WSL2/Bash（test 环境示例）：

```bash
cd /mnt/d/Project/wordloom-v3

export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export OUTBOX_WORKER_ID='c1'
export OUTBOX_METRICS_PORT=9110
export OUTBOX_BATCH_SIZE=50
export OUTBOX_POLL_INTERVAL_SECONDS=0.2
export OUTBOX_LEASE_SECONDS=30
export OUTBOX_MAX_ATTEMPTS=10
export OUTBOX_BASE_BACKOFF_SECONDS=0.5
export OUTBOX_MAX_BACKOFF_SECONDS=30
export OUTBOX_RECLAIM_INTERVAL_SECONDS=5
export OUTBOX_MAX_PROCESSING_SECONDS=600

python backend/scripts/chronicle_outbox_worker.py
```

---

## 7) Rebuild（读模型可重建）

- 目标：从 `chronicle_events` 全量重建 `chronicle_entries`。
- 直接写 entries（同步重建）：
	- `python backend/scripts/rebuild_chronicle_entries.py --truncate`
- 走 outbox + worker 路径（验证 worker）：
	- `python backend/scripts/rebuild_chronicle_entries.py --truncate --emit-outbox`
	- 然后启动 `chronicle_outbox_worker.py` 消费 outbox

---

## 8) 观测与告警（TODO：实验后填写阈值）

### 8.1 必看指标（参考 run-001/run-003 口径）

- outbox：lag / oldest_age / inflight
- retry：retry_scheduled_total
- terminal failed：terminal_failed_total（按 error_reason 维度聚合）
- rebuild（可选）：duration / last_finished / last_success

### 8.2 推荐告警（占位）

- oldest_age 超过 SLA
- terminal_failed_total 突增（按 error_reason 定位）
- stuck_processing_events > 0 且持续 N 分钟（如启用 lease/reclaim）

---

## 9) 常见故障处理（SOP 占位）

### 9.1 transient 错误（可重试）

- 预期行为：进入 pending + next_retry_at，backoff 收敛。
- 操作：确认依赖恢复后 backlog 回落。

### 9.2 deterministic 错误（必须修因）

- 预期行为：直接进入 failed（终态），写入 error_reason + error。
- 操作：按 error_reason 聚合 → 定位根因 → 修复后 replay。

---

## 10) 失败终态与 replay（可审计）

- replay 脚本：`backend/scripts/chronicle_outbox_replay_failed.py`
- 示例（把 failed 批量回到 pending，并写审计字段）：
	- `python backend/scripts/chronicle_outbox_replay_failed.py --limit 100 --by ops --reason "fix applied"`

最小验收：

- replay 之后：failed 的行变成 pending
- `replay_count + 1`
- `last_replayed_at/last_replayed_by/last_replayed_reason` 写入

---

## 11) 回归验证

- 回归入口：跑一遍 labs-005。
- 失败管理回归：复用 labs-004 的 v1–v4 思路（对 chronicle worker 复刻一遍）。
