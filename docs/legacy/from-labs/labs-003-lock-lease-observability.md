# Labs-003：Outbox lock + lease + SKIP LOCKED 小实验（操作指南 + 结论模板）

目标：用最小代价把三件事“跑出来、看见、写结论”。

- 行锁（`FOR UPDATE SKIP LOCKED`）：验证多 worker 抢单不重复。
- 租约（lease + reclaim）：验证 worker 死在半路也不会卡死。
- CAS（这里特指 outbox ack 的 guard）：验证“失去 owner / lease 过期”不会误 ack。

本实验基于当前实现：worker 在 [backend/scripts/search_outbox_worker.py](../../../../scripts/search_outbox_worker.py) 中使用：

- claim：`SELECT ... FOR UPDATE SKIP LOCKED` → `status=processing, owner=OUTBOX_WORKER_ID, lease_until=now()+OUTBOX_LEASE_SECONDS`
- reclaim：把 `processing AND lease_until < now()` 回收为 `pending`
- ack：`UPDATE ... WHERE owner=my_id AND status='processing' AND lease_until > now()`（guard 防“回魂写”）

---

## 0) 前置条件（必备）

### 0.1 需要哪些进程

- PostgreSQL（test DB）
- Elasticsearch
- API（用于产生 outbox；也可以用你已有脚本/数据）
- worker（本实验重点）
- 可选：Prometheus + Grafana（用于更舒服地看 metrics）

### 0.2 强烈建议：用 test 环境，避免混库

- 让 `WORDLOOM_ENV=test` 生效（`.env.test` 里通常有）
- worker 内部会做 DB 环境哨兵检查（如果你设置了 `WORDLOOM_ENV`）

---

## 1) 快速启动（建议路径）

### 1.1 启动 infra（ES + 可选监控）

从仓库根目录：

```bash
docker compose -f docker-compose.infra.yml --profile monitoring up -d
```

验证：

- Grafana: http://localhost:3000（admin/admin）
- Prometheus: http://localhost:9090
- ES: http://localhost:9200

### 1.2 启动 API + worker（使用 `.env.test`）

你已有 SOP 可参考 Labs-002。这里只强调实验需要的 worker 环境变量：

- `OUTBOX_WORKER_ID`：区分不同 worker
- `OUTBOX_LEASE_SECONDS`：租约秒数（实验建议设短一些）
- `OUTBOX_RECLAIM_INTERVAL_SECONDS`：回收扫描间隔
- `OUTBOX_METRICS_PORT`：本机多 worker 时必须不同

---

## 2) 观测点（你要盯哪些东西）

### 2.1 Metrics（不靠 Prometheus，也能 curl）

```bash
curl -s http://localhost:9109/metrics | egrep '^outbox_(lag_events|processed_total|failed_total)' || true
curl -s http://localhost:9109/metrics | egrep '^outbox_es_bulk_' || true
```

最关键：

- `outbox_lag_events{projection="search_index_to_elastic"}`：未处理积压（pending+processing）
- `outbox_processed_total` / `outbox_failed_total`：处理成功/失败累计

### 2.2 DB（最直观，建议每个场景都跑）

```sql
-- 状态分布
SELECT status, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL
GROUP BY status
ORDER BY status;

-- 谁持有 processing（多 worker 抢单时最关键）
SELECT owner, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL AND status='processing'
GROUP BY owner
ORDER BY count(*) DESC;

-- 是否存在“租约已过期但仍 processing”的 stuck
SELECT count(*) AS stuck_processing
FROM search_outbox_events
WHERE processed_at IS NULL
	AND status='processing'
	AND lease_until IS NOT NULL
	AND lease_until < now();
```

### 2.3 Logs（用于证明 reclaim）

worker 有一条非常关键的日志：

- `Reclaimed X expired outbox leases`

它是你判断“租约闭环生效”的最短证据链。

---

## 3) 产生 outbox 数据（负载脚本）

脚本：`backend/scripts/load_generate_blocks.py`（详见 Labs-002）

建议用 WSL2 / bash（和 Labs-002 一致）：

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

## 4) 实验 1：租约 + reclaim（单 worker 也能验证）

核心思路：让 worker 先 claim（行已变 processing），然后把 worker 杀掉。
重启 worker 后，reclaim 会把过期 lease 的 processing 回收成 pending，再继续处理。

### 4.1 启动 worker（租约设短一点）

WSL2 / bash：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-search-index-test'

export OUTBOX_WORKER_ID='w1'
export OUTBOX_METRICS_PORT=9109
export OUTBOX_LEASE_SECONDS=10
export OUTBOX_RECLAIM_INTERVAL_SECONDS=2
export OUTBOX_BULK_SIZE=200
export OUTBOX_POLL_INTERVAL_SECONDS=0.2

python3 scripts/search_outbox_worker.py
```

### 4.2 等待 claim 发生，然后立刻杀掉 worker

用 DB 观察 `processing` 出现后（owner=w1），立刻 `Ctrl+C` 结束 worker。

```sql
SELECT owner, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL AND status='processing'
GROUP BY owner;
```

### 4.3 等待 lease 过期，再重启 worker

等待 12~15 秒（大于 lease=10s），然后重新运行 4.1 的启动命令。

### 4.4 预期

- 日志出现：`Reclaimed X expired outbox leases`
- DB 中：`stuck_processing` 先 >0，随后回到 0
- `outbox_lag_events` 下降，`outbox_processed_total` 继续上升

### 4.5 结论记录（填空）

- 参数：`lease_seconds=10`，`reclaim_interval=2`，`batch_size=200`
- 现象：kill 后 processing 数量约为 `188`（`owner=w1`）
- 现象：重启后 pending/processing 查询结果为 0，且最终全量状态为 `done=125597`（本次未观察到 `pending/processing/failed` 残留）
- 判定：租约闭环是否生效？`是`
- 备注（异常/踩坑）：本次 worker 日志里 `Reclaimed X expired outbox leases` 的 X 未留存；下次可在重启后立刻截取该行，或在 DB 侧用 `stuck_processing` 查询在重启前后做对比。

---

## 5) 实验 2：ack guard（CAS 语义）验证（单 worker 可验证）

核心思路：在 worker 处理过程中，手工篡改一条 processing 行的 owner / lease。
正确实现应当保证：worker 不会把“已经不属于自己”的行 ack 成 done。

### 5.1 让 worker 正常跑起来（同实验 1 的启动即可）

确保有 processing 行：

```sql
SELECT id, owner, lease_until
FROM search_outbox_events
WHERE processed_at IS NULL AND status='processing'
ORDER BY updated_at DESC
LIMIT 5;
```

### 5.2 手工篡改 owner（模拟“被别的 worker 接管/污染”）

挑一条 `id`，执行：

```sql
UPDATE search_outbox_events
SET owner = 'evil-worker'
WHERE id = '<id>'
	AND status='processing'
	AND processed_at IS NULL;
```

可选：为了更快触发 reclaim，把 lease 改成过去：

```sql
UPDATE search_outbox_events
SET lease_until = now() - interval '1 minute'
WHERE id = '<id>'
	AND status='processing'
	AND processed_at IS NULL;
```

### 5.3 预期

- 该行不会被 w1 ack 成 done（`processed_at` 仍为 NULL）
- 如果 lease 被你改成过去：reclaim 会回收它（变回 pending）
- 如果 lease 仍在未来：它会保持 processing，直到 lease 过期被回收

额外自检（建议跑）：

```sql
-- 正常情况下应为 0。
-- 若 >0，说明存在“done 但 owner 未清理”的状态污染（可能来自手工篡改或代码路径缺陷）。
SELECT count(*)
FROM search_outbox_events
WHERE status='done' AND owner IS NOT NULL;
```

### 5.4 结论记录（填空）

- 被篡改的 `id=__`
- 篡改方式：`改 owner / 改 lease / 两者都改`
- 结果：该行最终状态流转：`processing -> __ -> __`
- 判定：ack guard 是否有效？`是 / 否`
- 备注：`__`

### 5.5 本次实验记录（2026-02-01，已完成）

你本次的关键操作是“只改 owner，不改 lease”。现象链路符合当前实现的设计预期：

- 初始：`status=processing, owner=w1`（worker 已 claim，持有租约）
- 手工篡改：`owner=evil-worker`（仅 owner 被污染）
- 由于 worker 的续租与 ack 都带 `WHERE owner=w1 ...` 的 guard：
	- worker **不会续租**（因为 owner 不再是 w1）
	- worker **不会 ack 成 done**（因为 owner 不再是 w1）
- 等到原租约自然过期（`lease_until < now()`）后：reclaim 会回收该行，使其重新可被领取
- 下一轮 claim：worker 再次把它领回（owner 重新变回 `w1`），继续正常处理，最终 `done` 且 `owner/lease_until=NULL`

你观察到的“evil-worker 很快变成 w1”，不是 guard 直接“改回” owner，而是：

- lease 到期 → reclaim → 重新 claim 的结果。

**本次结论（可直接抄）**

- 被篡改的 id：`38b3c7e3-230b-42d5-80a9-50653015214c`
- 篡改方式：`仅改 owner`
- 状态流转（观测）：`processing(w1) -> processing(evil-worker) -> processing(w1) -> done(owner=NULL)`
- 判定：ack guard 是否有效？`是`（错 owner 时不会被错误 ack；需要 lease 到期后才能被回收接管）

**踩坑记录（本次顺带修复）**

- 现象：曾出现 `status='done' AND owner IS NOT NULL` 的“终态污染”（计数为 1）。
- 原因：手工 UPDATE 未限制 `status='processing'` 时，可能在行已 done 之后仍把 owner 改成了 evil-worker，导致“done 但 owner 非空”。这不是业务正确性的必然 bug，但会干扰实验判读。
- 修复：
	- 实验 2 的篡改 SQL 增加 `AND status='processing' AND processed_at IS NULL`（避免误改终态）
	- 增加自检 SQL：`SELECT count(*) FROM search_outbox_events WHERE status='done' AND owner IS NOT NULL;`（应为 0）

---

## 6) 实验 3：SKIP LOCKED 抢单不重复（需要 2 个 worker）

核心思路：同机启动两个 worker（不同 `OUTBOX_WORKER_ID`、不同 metrics 端口），
观察 processing 的 owner 会分摊，且不会出现“同一批任务被两边同时 claim”。

### 6.1 启动 worker A（w1）

```bash
cd /mnt/d/Project/wordloom-v3/backend

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-search-index-test'

export OUTBOX_WORKER_ID='w1'
export OUTBOX_METRICS_PORT=9109
export OUTBOX_LEASE_SECONDS=30
export OUTBOX_RECLAIM_INTERVAL_SECONDS=5
export OUTBOX_BULK_SIZE=200
export OUTBOX_POLL_INTERVAL_SECONDS=0.2

python3 scripts/search_outbox_worker.py
```

### 6.2 启动 worker B（w2）

另开一个终端：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:9200'
export ELASTIC_INDEX='wordloom-search-index-test'

export OUTBOX_WORKER_ID='w2'
export OUTBOX_METRICS_PORT=9110
export OUTBOX_LEASE_SECONDS=30
export OUTBOX_RECLAIM_INTERVAL_SECONDS=5
export OUTBOX_BULK_SIZE=200
export OUTBOX_POLL_INTERVAL_SECONDS=0.2

python3 scripts/search_outbox_worker.py
```

### 6.3 制造竞争（再跑一波 loadgen）

```bash
cd /mnt/d/Project/wordloom-v3/backend

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export LOADGEN_SCENARIO=create
export TOTAL_OPS=8000
export CONTENT_BYTES=200
export RATE_PER_SEC=200
export CONCURRENCY=40

python3 scripts/load_generate_blocks.py
```

### 6.4 预期与验证（DB）

```sql
SELECT owner, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL AND status='processing'
GROUP BY owner
ORDER BY count(*) DESC;
```

预期：`w1`/`w2` 都会持有 processing（分摊）。

进一步：停掉 w1（Ctrl+C），等待 lease 过期后，w2 仍会把任务继续处理（接管闭环）。

### 6.5 结论记录（填空）

- w1/w2 配置差异：`OUTBOX_WORKER_ID`、`OUTBOX_METRICS_PORT` 不同（w1=9109，w2=9110）；其余 lease/reclaim/bulk 参数一致
- processing 分摊情况（owner->count）：观察到 `owner` 维度同时存在 `w1` 与 `w2`（证明抢单分摊）；当你 `Ctrl+C` 停掉 w1 后，processing 的 `owner` 逐步只剩 `w2`（证明接管发生）
- 停掉 w1 后，w2 是否能接管？`是`
- 证据（SQL/metrics/log）：
	- pending+processing 持续下降（截图 3→4：`pending 13756/processing 134` → `pending 10756/processing 67`）
	- 最终收敛：状态分布只剩 `done 170947`（截图 5）
	- stuck 自检：`stuck_processing`（`lease_until < now()` 且仍 processing）应为 `0`（用于证明“无过期租约卡死”）

### 6.6 本次实验记录（2026-02-01，已完成）

你本次在双 worker 并发下进行了“停掉 w1 → 验证 w2 接管 → 验证最终收敛”的闭环：

- 并发阶段：`w1` 与 `w2` 同时运行，processing 的 `owner` 可同时观察到 `w1`/`w2`（说明 `FOR UPDATE SKIP LOCKED` 下不会重复领取，并会自然分摊）
- 故障阶段：你 `Ctrl+C` 停掉 w1；此时 w1 已 claim 的 processing 行在租约到期后会被 reclaim 回收为 pending，随后由仍存活的 w2 继续 claim/处理
- 收敛阶段：pending/processing 数量持续下降并最终归零；最终全量状态仅剩 `done`（截图 5）

**本次结论（可直接抄）**

- 判定：多 worker 抢单不重复 `OK`；停掉一个 worker 后可在 lease 到期后被另一个 worker 接管 `OK`；最终收敛 `OK`

---

## 7) 可选：故意造 bug（仅用于教学，不建议长期保留）

目的：让你亲眼看到“没有锁/没有原子 claim”会发生什么。

建议方式：新开一个临时分支/临时改动，把 claim 的 `.with_for_update(skip_locked=True)` 去掉或改错，再重复实验 3。

预期：

- 两个 worker 可能会重复拿到同一批行（取决于隔离级别/时序）
- ES 会出现重复写、吞吐抖动、日志异常（“鬼故事”立刻显形）

结论记录（填空）：

- 你改动了什么：`__`
- 复现到的异常现象：`__`
- 你如何用“恢复锁+租约”消灭它：`__`

### 7.1 本次实验记录：实验 A（去掉 SKIP LOCKED，已完成）

你本次的实验 A 是“把 claim 从 `FOR UPDATE SKIP LOCKED` 改成普通 `FOR UPDATE`”，用来观察并发 worker 在锁竞争下的行为变化。

**观测到的现象（与你截图一致）**

- `processing` 的归属分摊明显变得不稳定且倾斜（示例）：
	- `w1=108, w2=78`
	- 随后变为 `w2=198, w1=24`
	这说明并发 worker 更容易出现阻塞/等待/抢不到锁的情况，导致“看起来像单 worker”或分摊很不均。
- `pg_stat_activity` 中出现 `wait_event_type=Lock` / `wait_event=transactionid`，且等待的 SQL 是 `INSERT INTO search_index(...)`。
	- 这条证据说明：并发写入路径里确实存在事务锁等待（不一定只来自 outbox claim；也可能来自 `search_index` 写入的冲突/约束等待）。
	- 若要“专门证明 claim 在等锁”，可以在 `pg_stat_activity.query` 中抓到包含 `search_outbox_events ... FOR UPDATE` 的那条查询；本次截图已经足够证明“锁等待增多/更明显”的方向性。

**本次结论（可直接抄）**

- 去掉 `SKIP LOCKED` 后，并发 worker 更容易互相阻塞/等待，processing 归属更不均衡，吞吐更抖或下降。
- `SKIP LOCKED` 的核心价值是：遇到已被锁住的行直接跳过而不是等待，从而提升并发下的稳定性与分摊公平性。

### 7.2 本次实验记录：实验 B1（破坏原子 claim，已完成）

你本次的实验 B1 是“故意破坏 claim 的原子性”，用来直观看到：两个 worker 在竞争时更容易读到同一批候选行，最终在处理阶段因为 `owner` 校验失败而被跳过（表现为明显的竞态浪费）。

**怎么复跑（关键开关）**

- 两个 worker 都要开启：
	- `OUTBOX_EXPERIMENT_BREAK_CLAIM=1`
	- `OUTBOX_EXPERIMENT_BREAK_CLAIM_SLEEP_SECONDS=0.2`（或更大，用于放大竞态窗口）

**观测到的现象（可量化证据链）**

- Metrics：`outbox_owner_mismatch_skips_total{projection="search_index_to_elastic"}` 明显增长。
	- 这是“worker 读到/准备处理，但发现 owner 已不是自己，于是 skip”的累计计数。
	- 你可以直接用 curl 取证：

	```bash
	curl -s http://localhost:9109/metrics | egrep '^outbox_owner_mismatch_skips_total' || true
	curl -s http://localhost:9110/metrics | egrep '^outbox_owner_mismatch_skips_total' || true
	```

- Logs（节流输出）：在 break 模式下，worker 会每 5 秒打印一次 “owner mismatch 被跳过” 的汇总 warning（含累计 skip 数与最近 event id/owner）。
	- 这条日志是对上面 counter 的“人类可读版本”，便于截图与写结论。

**本次结论（可直接抄）**

- 破坏原子 claim 后，两个 worker 更容易在竞争窗口内对同一批候选行产生竞态，导致处理阶段出现大量 `owner mismatch skip`。
- `outbox_owner_mismatch_skips_total` 的持续增长与节流 warning 日志共同证明：该模式会带来显著的重复读取/无效工作（浪费吞吐），而正确的原子 claim（行锁 + 一次性更新）可以消除这类竞态浪费。

---

## 8) 最后总结（写给未来的你）

- 锁（SKIP LOCKED）解决“重复领取”。
- 租约（lease+reclaim）解决“死亡卡死”。
- ack guard 解决“回魂写坏结果”。

正确性很多时候只能在“竞争/故障”里被看见；
这份 Labs 的目的就是让你能稳定复现、稳定消灭。