可以把“故意造 bug”做成两种层级：A 只去掉 SKIP LOCKED（更安全、主要展示吞吐/阻塞问题），B 破坏“原子 claim”（更危险、能展示重复处理/争抢写）。建议你按 A→B 的顺序做，且只在 test DB + 临时分支 上操作。

A) 去掉 SKIP LOCKED：观察“阻塞/吞吐下降”（推荐先做这个）
1) 建临时分支

cd /mnt/d/Project/wordloom-v3
git checkout -b labs003-break-skip-locked

2) 改 worker 的 claim：把 skip_locked=True 去掉
在 search_outbox_worker.py 里搜索：

with_for_update(
或 FOR UPDATE SKIP LOCKED
把它从类似：

with_for_update(skip_locked=True)
改为：
with_for_update()（或 skip_locked=False）
目标：两 worker 同时抢同一批行时，一个会被锁阻塞，不再“各拿各的”。

3) 复现实验
启动 w1、w2（同实验 3）
跑 loadgen 制造积压
4) 观测点（你会看到什么）
DB：

-- 正常(SKIP LOCKED)时：w1/w2 通常都会有 processing
SELECT owner, count(*)
FROM search_outbox_events
WHERE processed_at IS NULL AND status='processing'
GROUP BY owner
ORDER BY count(*) DESC;

现象预期（去掉 SKIP LOCKED 后）：

可能长期只有一个 worker 在干活（另一个卡在等锁）
outbox_lag_events 下降变慢、抖动变大
worker 日志可能出现“某次循环卡很久”（因为在等行锁）
5) 回滚

git restore backend/scripts/search_outbox_worker.py
git switch -

B) 破坏“原子 claim”：观察“重复处理/错写”（危险但更有教学价值）
注意：如果你当前实现是 “SELECT … FOR UPDATE … 然后在同一事务里 UPDATE 把 status/owner/lease 写进去”，那其实非常稳；要造出“重复处理”，通常得把它改成 非原子两步。

1) 造 bug 的典型改法（思路，不建议长期保留）
把 claim 变成这种反模式：

先 SELECT id FROM ... WHERE status='pending' LIMIT N（不加锁）
再逐条 UPDATE ... SET status='processing', owner=:me ... WHERE id=:id（如果还不加 AND status='pending'，更容易乱）
这样在并发下，w1/w2 可能读到同一批 pending，进而都尝试处理（即使最后 DB 状态只显示一个 owner，也可能出现“重复对 ES 写”的副作用）。

2) 如何验证“重复处理”确实发生
优先看日志（最直观）：

在“开始处理事件”处打印 worker_id + ev.id（两边若出现同一个 ev.id，就是重复处理）
其次看 ES 写入次数/冲突（看你的 ES bulk 指标或日志里同 doc_id 的重复 upsert）。

你写到 Lab-003 里的建议结论模板（对应 A / B）
A（只去掉 SKIP LOCKED）：不会必然重复处理，但会出现阻塞/吞吐下降/分摊消失（owner 分布更单边）
B（破坏原子 claim）：可能出现重复处理（两 worker 处理同一 ev.id / 同一 doc_id 被重复 upsert）
我需要你给我 2 个信息，我就能把“7) 可选：故意造 bug”写得更贴合你仓库
search_outbox_worker.py 里 claim 那段代码（含 with_for_update/SQL 片段）贴出来
你希望第 7 节更偏向哪种演示：阻塞吞吐(A) 还是 重复处理(B)

0) 造流
cd /mnt/d/Project/wordloom-v3/backend

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export LOADGEN_SCENARIO=create
export TOTAL_OPS=3000
export CONTENT_BYTES=200
export RATE_PER_SEC=100
export CONCURRENCY=20

python3 scripts/load_generate_blocks.py

1) 启动 worker A（w1）
cd /mnt/d/Project/wordloom-v3/backend
set -a; source .env.test; set +a

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

2) 启动 worker B（w2）
另一个新终端（WSL）：
cd /mnt/d/Project/wordloom-v3/backend
set -a; source .env.test; set +a

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

3) 制造竞争（跑负载，让 outbox 积起来）
另开一个终端（WSL）：
cd /mnt/d/Project/wordloom-v3/backend
set -a; source .env.test; set +a

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export LOADGEN_SCENARIO=create
export TOTAL_OPS=8000
export CONTENT_BYTES=200
export RATE_PER_SEC=200
export CONCURRENCY=40

python3 scripts/load_generate_blocks.py