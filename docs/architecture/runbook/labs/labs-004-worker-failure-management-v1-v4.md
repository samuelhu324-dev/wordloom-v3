# Labs-004：Outbox worker 失败管理（v1 → v4）小实验（操作指南 + 结论模板）

目标：在演化成 Runbook（例如 run-002）之前，先用“手工可控实验”把失败管理跑出来、看见、写结论。
完成后再把实验结论沉淀成可追查/可复用的运行手册。

本实验覆盖的能力分层：

- v1：stuck 自愈（lease + max processing）
- v2：错误收敛（fail-safe default + max_attempts + reason + last error + metrics）
- v3：可运营的失败（DLQ/failed 可检索 + 显式 replay + 审计）
- v4：daemon 运行时工程化（graceful shutdown / health / readiness / 告警）

本实验基于当前实现：

- worker：`backend/scripts/search_outbox_worker.py`
- replay：`backend/scripts/search_outbox_replay_failed.py`
- 环境矩阵：`docs/ENVIRONMENTS.md`（dev/test=localhost:5435；ES=localhost:9200）

---

## 0) 前置条件（必备）

### 0.1 需要哪些进程

- PostgreSQL（dev/test DB：localhost:5435）
- Elasticsearch（localhost:9200）
- API（用于产生 outbox；或用 loadgen 脚本产生变更）
- Outbox worker（本实验重点）
- 可选：Prometheus + Grafana（更舒服地看 metrics）

### 0.2 强烈建议：用 test 环境跑实验

- `DATABASE_URL=postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test`
- `WORDLOOM_ENV=test`
- `OUTBOX_METRICS_PORT=9109`（避免和 dev 冲突）

---

## 1) 快速启动（建议路径）

### 1.1 起 DB（Windows PowerShell）

从仓库根目录：

```powershell
./backend/scripts/devtest_db_5435_start.ps1
```

### 1.2 起 ES（Windows PowerShell）

从仓库根目录：

```powershell
docker compose -f docker-compose.infra.yml up -d es
```

可选：加监控

```powershell
docker compose -f docker-compose.infra.yml --profile monitoring up -d
```

### 1.3 起 API（WSL2 / bash；建议 test 端口 30011）

此处不重复 SOP（见 `docs/ENVIRONMENTS.md` / QUICK_COMMANDS）。

### 1.4 起 worker（WSL2 / bash）

最小启动：

```bash
cd /mnt/d/Project/wordloom-v3

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-test-search-index'

export OUTBOX_WORKER_ID='w1'
export OUTBOX_METRICS_PORT=9109

python backend/scripts/search_outbox_worker.py
```

---

## 2) 观测点（每个场景都跑，做“事实裁判”）

### 2.1 Metrics（不靠 Prometheus，也能 curl）

```bash
curl -s http://localhost:9109/metrics | egrep '^outbox_(lag_events|oldest_age_seconds|inflight_events|processed_total|failed_total|stuck_processing_events|retry_scheduled_total|terminal_failed_total)' || true
```

最关键（按优先级）：

- `outbox_lag_events{projection="search_index_to_elastic"}`：积压（pending+processing）
- `outbox_oldest_age_seconds{...}`：最老事件年龄（新鲜度）
- `outbox_stuck_processing_events{...}`：stuck 数（v1）
- `outbox_retry_scheduled_total{...}`：安排重试次数（v2）
- `outbox_terminal_failed_total{...}`：进入终态 failed 的次数（v2）

### 2.2 DB 快照（最准确，建议每个场景都跑）

```sql
-- A) 状态分布（看系统是否推进/是否被 failed 拖死）
SELECT status, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL
GROUP BY status
ORDER BY status;

-- B) stuck 自检（v1 核心验收）
-- 说明：lease 过期 或 处理超时 即视为 stuck
SELECT count(*) AS stuck_processing
FROM search_outbox_events
WHERE processed_at IS NULL
	AND status='processing'
	AND (
		(lease_until IS NOT NULL AND lease_until < now())
		OR (
			processing_started_at IS NOT NULL
			AND now() - processing_started_at > interval '10 minutes'
		)
	);

-- C) 最老 pending（判断 backoff/next_retry_at 是否工作）
SELECT id, created_at, attempts, next_retry_at, error_reason
FROM search_outbox_events
WHERE processed_at IS NULL AND status='pending'
ORDER BY created_at ASC
LIMIT 5;
```

### 2.3 Logs（用于证明“系统在自愈/在收敛”）

关键日志（示例）：

- reclaim：`Reclaimed ... stuck outbox events (expired lease or max processing exceeded)`
- bulk 部分失败：会有 bulk failure class 统计（配合 metrics 更好）

---

## 3) 产生 outbox 数据（负载脚本）

推荐：用现成 loadgen（详见 labs-003）。示例：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export LOADGEN_SCENARIO=create
export TOTAL_OPS=3000
export CONTENT_BYTES=200
export RATE_PER_SEC=100
export CONCURRENCY=20

python3 scripts/load_generate_blocks.py
```

---

## 4) 实验 1（v1）：Kill worker 后能自动自愈（reclaim）

### 4.1 目的

验证：worker 半路死亡/卡死不会让 outbox 永久悬空。

### 4.2 建议参数（把 lease 设短一点，验证更快）

```bash
export OUTBOX_LEASE_SECONDS=10
export OUTBOX_RECLAIM_INTERVAL_SECONDS=2
export OUTBOX_MAX_PROCESSING_SECONDS=60
```

### 4.3 步骤

1) 确保 outbox 有 pending（跑一波 loadgen）
2) 启动 worker，让它进入 processing（`status='processing'` 出现）
3) 立刻 kill worker（Ctrl+C 或直接杀进程）
4) 等待 lease/max_processing 超过阈值
5) 重启 worker（同 1.4 启动命令）

### 4.4 预期

- DB：stuck 计数会短暂 >0，随后回到 0
- logs：出现 reclaim 相关日志
- metrics：`outbox_stuck_processing_events` 回落到 0，`outbox_processed_total` 继续增长

### 4.5 结论记录（填空）

- 参数：lease=__s, reclaim_interval=__s, max_processing=__s
- kill 时 processing 约为：__
- 重启后 stuck 是否归零：`是/否`
- 判定：v1 stuck 自愈 `OK/FAIL`

### 4.6 实验记录（已执行：2026-02-03）

实验环境：

- DB：`wordloom_test`（localhost:5435）
- 观测：VS Code DBClient 直接跑 SQL（见下方快照）

#### 4.6.1 实验过程（你实际做的动作）

1) 产生 outbox（让 `pending/processing` 出现）
2) worker 正在处理时，**强制 kill** worker（模拟 crash/断电）
3) 等待 lease 到期（或超过 max_processing_seconds）
4) 重启 worker，观察 reclaim 是否把 stuck 捞回并继续推进

#### 4.6.2 DB 快照（kill 后的观测）

状态分布：

```sql
select status, count(*)
from search_outbox_events
group by status
order by status;
```

你观测到（kill 后）：

- `done = 246547`
- `pending = 756`
- `processing = 50`

stuck 扫描（v1 核心验收）：

```sql
select count(*) as stuck
from search_outbox_events
where status='processing'
	and (
		lease_until < now()
		or (processing_started_at is not null and now() - processing_started_at > make_interval(secs => 600))
	);
```

你观测到（kill 后）：

- `stuck = 50`

解释：这批 `processing` 事件在 crash 后不会被正常 ack，等 lease 过期后就会被识别为 stuck。

#### 4.6.3 DB 快照（恢复完成后的观测）

你观测到（恢复完成后）：

- `stuck = 0`（没有残留）
- `done` 从 `246547` 增长到 `247353`（系统恢复推进，累计 +806）
- `pending/processing` 最终归零（队列没有被永久卡住）

#### 4.6.4 判定

- 重启后 stuck 归零：`是`
- 判定：v1 stuck 自愈 `OK`

---

## 5) 实验 2（v2）：ES 不可用（连接错误/5xx）→ retry 收敛

### 5.1 目的

验证：暂时性故障会进入 pending + next_retry_at，且带 backoff+jitter，队列不会“自残式狂刷”。

### 5.2 步骤（最稳定复现）

1) 正常启动 worker
2) 让 ES 不可用（二选一）：

- 停掉 ES：`docker compose -f docker-compose.infra.yml stop es`
- 或把 worker 的 `ELASTIC_URL` 改成一个错误地址再启动

3) 观察 2~3 分钟

### 5.3 预期

- 指标：`outbox_retry_scheduled_total` 持续增长
- DB：pending 行 `next_retry_at` 会被推迟；attempts 增长但不会每秒爆炸
- 终态 failed 不应大量增长（除非你也注入了确定性错误）

### 5.4 结论记录（填空）

- 故障注入方式：停 ES / 错 URL
- retry 指标是否增长：`是/否`
- attempts 是否可控：`是/否`
- 判定：v2 backoff+jitter `OK/FAIL`

### 5.5 实验记录（已执行：2026-02-03）

说明：这次实际操作是“**处理中途关 ES，后续再开**”的路径；由于 ES 断开时间较长，实验过程中不仅验证了 v2 的 retry/backoff，也自然触发了实验 4（达到 max_attempts 后转 failed）。

#### 5.5.1 实验过程（你实际做的动作）

1) 造流（产生 outbox 事件）
2) worker 正常处理过程中，**中途 stop ES**（模拟依赖瞬断/宕机）
3) 观察 pending/processing 分布、attempts 增长、next_retry_at 推迟到未来
4) 后续 **start ES**（恢复依赖）

#### 5.5.2 关键观测（你截图里的事实）

- 出现了 `attempts=8/9` 的事件（你说中途出现过 8、9，只是部分没截到）
- pending 行可见 `next_retry_at`（推迟到未来），并且出现 `error_reason=connect`（连接类错误）
- 这说明：失败后确实进入了 retry/backoff 路径（不是“每秒疯狂重试直到把系统打爆”）

#### 5.5.3 判定（实验 2）

- retry/backoff 机制：`OK`
- 备注：如果希望“只验证实验 2、不触发实验 4”，建议把 ES 断开控制在更短时间（例如 30~60 秒），或临时把 `OUTBOX_MAX_ATTEMPTS` 提高。

---

## 6) 实验 3（v2）：确定性错误（4xx/坏 payload）→ 直接 failed（终态）

### 6.1 目的

验证：确定性错误不会无限重试，直接进入终态 failed，并记录 `error_reason + error`。

### 6.2 步骤 A（推荐：手工插入坏 outbox 记录；100% 可控）

说明：这一步是“实验注入”，不要求真实业务链路产生。

1) 用 SQL 插入一条故意坏数据（示例：非法 op），让 worker 在处理时抛 `ValueError`：

```sql
-- 注意：以当前仓库表结构为准（search_outbox_events 没有 projection 列）。
-- 另外 event_version / replay_count 在你的库里是 NOT NULL 且可能没有默认值，建议显式填 0。
INSERT INTO search_outbox_events (
	id,
	entity_type,
	entity_id,
	op,
	event_version,
	status,
	attempts,
	replay_count,
	created_at,
	updated_at
) VALUES (
	gen_random_uuid(),
	'block',
	gen_random_uuid(),
	'not-a-real-op',
	0,
	'pending',
	0,
	0,
	now(),
	now()
);
```

2) 启动 worker，等待它处理

### 6.3 预期

- DB：该行进入 `status='failed'`（终态），且 `error_reason` 有值（预期为 deterministic 相关）
- 指标：`outbox_terminal_failed_total{reason=...}` 增长

### 6.4 结论记录（填空）

- 注入方式：坏 op SQL
- failed 是否进入终态：`是/否`
- error_reason 是否写入：`是/否`（值：__）
- 判定：确定性错误收敛 `OK/FAIL`

### 6.5 实验记录（已执行：2026-02-03）

注入方式：向 `search_outbox_events` 插入一条非法 `op='not-a-real-op'` 的事件（你这次为便于定位，使用了固定 id：`11111111-1111-1111-1111-111111111111`）。

worker 日志关键事实（确定性异常）：

- `ValueError: Unknown outbox op: 'not-a-real-op'`

DB 关键观测（该条事件）：

- `status='failed'`（直接进入终态）
- `attempts=1`
- `next_retry_at IS NULL`（没有进入 backoff 重试队列）
- `error_reason='deterministic_exception'`
- `error` 字段包含 `Unknown outbox op: 'not-a-real-op'`

备注：你截图里同时能看到一些 `attempts=10`、`error_reason='unknown_exception'` 的 failed 行，那些是你之前跑实验 2/4 时累计出来的，不属于本次实验 3 的注入样本。

判定（实验 3）：确定性错误收敛 `OK`

---

## 7) 实验 4（v2）：max_attempts 到顶 → 自动转 failed（禁止无限重试）

### 7.1 目的

验证：不允许无限重试，到顶后进入终态 failed。

### 7.2 建议参数（把 max_attempts 设小，验证更快）

```bash
export OUTBOX_MAX_ATTEMPTS=3
export OUTBOX_BASE_BACKOFF_SECONDS=0.2
export OUTBOX_MAX_BACKOFF_SECONDS=1.0
```

### 7.3 步骤

1) 让 ES 不可用（见实验 2）
2) 观察同一批事件 attempts 增长
3) 等到 attempts 达到 max_attempts

### 7.4 预期

- DB：这些行最终进入 `status='failed'`
- 指标：`outbox_terminal_failed_total` 增长

### 7.5 实验记录（已执行：2026-02-03；与实验 2 同一轮操作）

触发方式：ES 断开时间较长，导致同一批事件 attempts 持续增长，最终部分事件被系统按上限策略收敛到 `failed`。

你观测到的现象：

- attempts 出现 `8/9`（达到上限附近/到顶）
- 状态分布中出现明显的 `failed`（同时仍能看到部分 `pending/processing`）

判定（实验 4）：

- max_attempts 上限策略生效：`OK`
- 备注：这也是“fail-safe default + 有上限”的核心价值——ES 长时间不可用时不会无限自残式重试，最终会把问题收敛为可运营的 failed 终态。

---

## 8) 实验 5（v3）：显式 replay failed → pending（可审计）

### 8.1 目的

验证：failed 对系统是终态；运维通过 replay 把 failed 重新回到 pending，并写审计字段。

### 8.2 步骤

1) 先制造一些 failed（实验 3/4 都可）
2) dry-run 看匹配量：

```bash
cd /mnt/d/Project/wordloom-v3

export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
python backend/scripts/search_outbox_replay_failed.py --by alice --reason "fixed root cause" --limit 100 --dry-run
```

3) 真正 replay：

```bash
python backend/scripts/search_outbox_replay_failed.py --by alice --reason "fixed root cause" --limit 100
```

### 8.3 预期

- DB：failed 行回到 pending，attempts/next_retry_at/error/error_reason 清理
- DB：`replay_count` +1，`last_replayed_at/by/reason` 写入

---

## 9) 实验 6（v4，占位）：daemon 运行时工程化（待实现后补充）

说明：当前仓库 worker 还没有完整的 v4 形态（health/readiness/graceful shutdown/告警阈值）。
当你把 v4 做完后，把下面 TODO 填上即可。

- TODO：SIGTERM graceful shutdown（停止 claim，尽量处理完当前批次）
- TODO：/healthz + /readyz（至少包含 DB/ES 连通性 + last_success freshness）
- TODO：报警阈值（oldest_age 超 SLA、stuck>0、terminal_failed 激增）

---

## 10) 最后总结（写给未来的你）

- v1 解决：卡死/崩溃后不会永久悬空（stuck 自愈）
- v2 解决：错误会收敛（fail-safe + 上限 + reason+last error）
- v3 解决：人能介入且可审计（replay）
- v4 解决：能长期跑（daemon 工程化）

这份 labs 的价值是：每次你改 worker/指标/迁移，都能用同一套实验在 10 分钟内确认没有退化。