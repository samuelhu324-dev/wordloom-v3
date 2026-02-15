
# LABS-001：Throughput / Lag Events 可观测性实验（blocks 造流）

目标：在本地 `wordloom_test` 环境里持续创建 blocks，驱动 outbox 产生事件并由 worker 投影到 Elasticsearch，然后用 `produced / processed / lag` 三条线观察吞吐与囤积。

这份实验假设你已经有：

- devtest Postgres（host 5435，包含 `wordloom_dev` + `wordloom_test`）
- infra-only compose 管理 Elasticsearch（以及可选 Prometheus/Grafana）
- API / outbox worker / loadgen 脚本可以在 WSL2 里运行

推荐环境：**依赖用 Docker，代码用 WSL2**（减少 Windows/WSL 混用导致的诡异行为）。

---

## 一、实验准备（依赖服务）

### 1) 启动 Elasticsearch（infra-only compose）

在仓库根目录执行：

```bash
cd /mnt/d/Project/wordloom-v3

# 只起 ES
docker compose -f docker-compose.infra.yml up -d es

# 可选：同时起 Prometheus + Grafana
# docker compose -f docker-compose.infra.yml --profile monitoring up -d
```

检查 ES：

```bash
curl -sS http://localhost:9200/_cluster/health?pretty | sed -n '1,30p'
```

### 2) 启动 Postgres（devtest-db-5435）

Windows PowerShell（仓库根目录）：

```powershell
cd d:\Project\wordloom-v3
.\backend\scripts\devtest_db_5435_start.ps1
```

> 注意：`wordloom_test` 只在新 volume 初始化时自动创建；如果你重置过 volume，记得先重新 migrate。

---

## 二、启动实验进程（test 环境）

本实验推荐用 `.env.test`（仓库根目录）来固定变量，避免环境混淆：

- `DATABASE_URL=.../wordloom_test`
- `ELASTIC_URL=http://localhost:9200`
- `ELASTIC_INDEX=wordloom-test-search-index`
- `WORDLOOM_ENV=test`（启用“防混库保险丝”，连错库会直接拒绝启动）

### 1) 启动 API（test：30011）

WSL2 / bash：

```bash
cd /mnt/d/Project/wordloom-v3/backend

./scripts/run_api.sh .env.test
```

### 2) 启动 outbox worker（test：metrics 9109）

WSL2 / bash：

```bash
cd /mnt/d/Project/wordloom-v3/backend

./scripts/run_worker.sh .env.test
```

可选：开启“真正的 ES Bulk API”（每轮 poll 发 1 次 `POST /_bulk`）

- 方式 A：直接在启动前临时 export

```bash
export OUTBOX_USE_ES_BULK=1
./scripts/run_worker.sh .env.test
```

- 方式 B：写进 `.env.test`（推荐，避免忘）

```text
OUTBOX_USE_ES_BULK=1
```

> 注意：Bulk 模式下 worker 每轮只发一个 bulk 请求，`OUTBOX_CONCURRENCY` 会被忽略（以日志提示为准）。

---

## 三、观测面板（不依赖 Prometheus 也能跑）

### 1) API 侧：produced（写入侧产出）

```bash
curl -s http://localhost:30011/metrics | egrep '^outbox_produced_total' || true
```

### 2) worker 侧：processed/failed/lag（消费侧）

```bash
curl -s http://localhost:9109/metrics | egrep '^outbox_(processed_total|failed_total|lag_events)' || true
```

Bulk 指标（bulk latency / request result / item failures）：

```bash
curl -s http://localhost:9109/metrics | egrep '^outbox_es_bulk_' || true
```

### 3) DB 侧：积压（最准）

```bash
psql "postgresql://wordloom:wordloom@localhost:5435/wordloom_test" \
	-c "select count(*) as pending from search_outbox_events where processed_at is null;"
```

> PowerShell 提醒：不要把 `/metrics` 输出误粘贴成脚本跑。
> Windows 下建议用：`curl.exe http://localhost:30011/metrics | findstr outbox_`

---

## 四、造流（批量创建 blocks）

### 1) 小流量 smoke（先保证链路通）

WSL2 / bash：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export TOTAL_BLOCKS=50
export CONCURRENCY=2
export RATE_PER_SEC=5
export BLOCK_TYPE=text
export CONTENT_BYTES=200
export REQUEST_TIMEOUT_S=60

export FAIL_SUMMARY_EVERY=10
export FAIL_SUMMARY_TOP_N=6
export FAIL_SUMMARY_SAMPLES=2
export FAIL_LINE_COMPACT=0

python3 scripts/load_generate_blocks.py
```

预期：

- API 的 `outbox_produced_total{... entity_type="block" ...}` 增长
- worker 的 `outbox_processed_total{projection="search_index_to_elastic"}` 增长
- `outbox_lag_events` 会在瞬间上升，然后回落/趋稳（取决于吞吐）

### 2) 压测/造囤积（调参训练）

示例：让 produced/s 持续大于 processed/s，观察 lag 上升。

```bash
export TOTAL_BLOCKS=5000
export CONCURRENCY=10
export RATE_PER_SEC=50
python3 scripts/load_generate_blocks.py
```

你可以通过以下手段“造囤积”或“消囤积”：

- **造囤积**：提高 `RATE_PER_SEC` 或 `CONCURRENCY`（写入侧更快）
- **消囤积**：提高 worker 的 `OUTBOX_BULK_SIZE`，降低 `OUTBOX_POLL_INTERVAL_MS`

如果你开启了 `OUTBOX_USE_ES_BULK=1`：

- `OUTBOX_CONCURRENCY` 基本不再是主要旋钮（每轮只有 1 个 bulk 请求）
- 更建议调 `OUTBOX_BULK_SIZE` 与 `OUTBOX_POLL_INTERVAL_MS`

（worker 参数可写在 `.env.test` 或在启动 worker 前临时 export。）

---

## 五、验证 Elasticsearch 结果（可选但推荐）

确认 index 内文档数量（test index）：

```bash
curl -sS "http://localhost:9200/wordloom-test-search-index/_count?pretty"
```

做一个简单搜索（loadgen content 默认包含 `loadgen block seq=...`）：

```bash
curl -sS "http://localhost:9200/wordloom-test-search-index/_search?q=loadgen&pretty" | sed -n '1,120p'
```

---

## 六、实验判读（你应该看到什么）

1）吞吐：

- produced/s：由 API `/metrics` 的 `outbox_produced_total` 推算（Prometheus 用 `rate()` 更直观）
- processed/s：由 worker `/metrics` 的 `outbox_processed_total` 推算

2）囤积：

- `outbox_lag_events`（worker 侧）持续上升：说明 processed/s < produced/s
- `outbox_lag_events` 趋稳/下降：说明 processed/s ≥ produced/s

3）失败：

- `outbox_failed_total` 增长：优先看 worker 日志（常见是 ES 不可达、index 名不对、网络重置）

4）Bulk 下游健康（开启 `OUTBOX_USE_ES_BULK=1` 时）：

- bulk 耗时：`outbox_es_bulk_request_duration_seconds`（Prometheus 可用 `histogram_quantile()` 看 p95）
- bulk 请求是否 partial：`outbox_es_bulk_requests_total{result="partial"}`
- 失败类别：`outbox_es_bulk_item_failures_total{failure_class="429"|"4xx"|"5xx"|"unknown"}`

---

## 七、截图2要求：每次实验固定做“服务存活检查”（强烈建议）

建议每次实验固定加 2~3 个 quick check（手动也行，后续可以写 smoke 脚本）：

```bash
# ES 活着没
curl -fsS http://localhost:9200 >/dev/null

# API 活着没（如果你实现了 health endpoint）
curl -fsS http://localhost:30011/healthz >/dev/null

# worker 进程还在不在（metrics 端口能不能访问）
curl -fsS http://localhost:9109/metrics >/dev/null
```

如果其中任何一个挂了：**先按“服务断了”处理**，不要先往“瓶颈/吞吐”方向解释。

> 备注：如果当前 API 没有 `/healthz`，可以临时用 `/metrics` 或 `/docs` 代替：
> - `curl -fsS http://localhost:30011/metrics >/dev/null`
> - `curl -fsS http://localhost:30011/docs >/dev/null`

