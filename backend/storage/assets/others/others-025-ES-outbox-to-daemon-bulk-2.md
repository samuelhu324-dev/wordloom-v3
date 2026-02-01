# ES outbox worker bulk 调参：多工况实验 SOP（create/update/delete/mixed）

目标：不只跑 `create_blocks`，而是用多种“负载形态 + 操作类型 + 失败形态”训练/验证 bulk 调参策略，并能在 worker `/metrics` 里用 bulk 指标分型。

本 SOP 假设你已经：

- 用 `.env.test` 跑 API + worker（`WORDLOOM_ENV=test` 防混库）
- worker 开启 `OUTBOX_USE_ES_BULK=1`

---

## 0) 统一开关与观测

### 启动 worker（bulk 模式）

WSL2 / bash：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export OUTBOX_USE_ES_BULK=1
export OUTBOX_BULK_SIZE=500
export OUTBOX_POLL_INTERVAL_MS=200

./scripts/run_worker.sh .env.test
```

### 快速看指标（不用 Prometheus 也能跑）

```bash
# bulk 指标
curl -s http://localhost:9109/metrics | egrep '^outbox_es_bulk_' || true

# produced / processed / lag
curl -s http://localhost:9109/metrics | egrep '^outbox_(processed_total|failed_total|lag_events)' || true
curl -s http://localhost:30011/metrics | egrep '^outbox_produced_total' || true
```

---

## 1) 负载脚本（多工况）

脚本：`backend/scripts/load_generate_blocks.py`

关键环境变量：

- `LOADGEN_SCENARIO`：`create` | `create_then_update` | `create_then_delete` | `mixed`
- `TOTAL_OPS`（或旧名 `TOTAL_BLOCKS`）：总操作次数（不含预创建 pool）
- `POOL_SIZE`：update/delete/mixed 的预创建 block 数
- `HOTSET_SIZE`：update 的“热 key”子集大小（越小越热）
- `MIX_CREATE_RATIO / MIX_UPDATE_RATIO / MIX_DELETE_RATIO`：mixed 分布（可开 `MIX_NORMALIZE=1` 自动归一）

通用必备：

```bash
cd /mnt/d/Project/wordloom-v3/backend

export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export CONCURRENCY=10
export RATE_PER_SEC=50
export BLOCK_TYPE=text
export REQUEST_TIMEOUT_S=60
```

---

## 2) 工况 A：create（小文档 vs 大文档）

### A1. 小文档稳态（基线）

```bash
export LOADGEN_SCENARIO=create
export TOTAL_OPS=5000
export CONTENT_BYTES=200

python3 scripts/load_generate_blocks.py
```

### A2. 大文档稳态（吞吐下降 + bulk latency 抬升）

```bash
export LOADGEN_SCENARIO=create
export TOTAL_OPS=2000
export CONTENT_BYTES=5000

python3 scripts/load_generate_blocks.py
```

看什么：

- `outbox_es_bulk_request_duration_seconds_*`（大文档会明显变慢）
- `outbox_lag_events` 是否开始持续上升

---

## 3) 工况 B：burst（突发）

目的：验证 lag 的上升/回落（策略的追赶能力），以及 bulk latency 是否越过阈值。

```bash
# 低速 60s 左右（手动跑一段即可）
export LOADGEN_SCENARIO=create
export TOTAL_OPS=2000
export CONTENT_BYTES=200
export RATE_PER_SEC=10
export CONCURRENCY=5
python3 scripts/load_generate_blocks.py

# 突发（更高的 produced）
export TOTAL_OPS=4000
export RATE_PER_SEC=120
export CONCURRENCY=20
python3 scripts/load_generate_blocks.py
```

---

## 4) 工况 C：update（热 key / 重复写）

目的：覆盖“重复更新同一批 doc”的形态（更贴近真实编辑），并用 `HOTSET_SIZE` 控制热度。

```bash
export LOADGEN_SCENARIO=create_then_update

# 先预创建 POOL_SIZE 个 blocks（脚本会自动做）
export POOL_SIZE=500
export HOTSET_SIZE=25

# 然后执行 TOTAL_OPS 次 update
export TOTAL_OPS=5000
export CONTENT_BYTES=400

python3 scripts/load_generate_blocks.py
```

看什么：

- bulk latency 是否显著抬升
- `outbox_es_bulk_requests_total{result="partial"}` 是否出现
- `outbox_es_bulk_item_failures_total{failure_class="4xx"|"5xx"|"429"}` 是否升高

---

## 5) 工况 D：delete（清理/回收）

目的：覆盖 delete item（payload 更小、语义不同）。脚本把 404 当作幂等成功。

```bash
export LOADGEN_SCENARIO=create_then_delete
export POOL_SIZE=2000
export TOTAL_OPS=2000

python3 scripts/load_generate_blocks.py
```

---

## 6) 工况 E：mixed（create/update/delete 混合）

目的：更贴近真实系统（编辑 + 新增 + 删除同存）。

```bash
export LOADGEN_SCENARIO=mixed
export POOL_SIZE=800
export HOTSET_SIZE=40
export TOTAL_OPS=8000

export MIX_CREATE_RATIO=0.55
export MIX_UPDATE_RATIO=0.35
export MIX_DELETE_RATIO=0.10
export MIX_NORMALIZE=1

python3 scripts/load_generate_blocks.py
```

---

## 7) 失败形态：复现 429（ES 吃不下）

目的：让 `failure_class="429"` 跑出来，用于验证策略的“降速/退避”逻辑。

### 方式：限制 ES 资源 + 提高造流

（示例命令，容器名以你实际为准）

```bash
docker ps --format '{{.Names}}' | grep -E 'es|elastic' || true
```

然后：

```bash
# 限制 ES 资源（示例）
docker update --cpus 0.5 --memory 1g <your_es_container>

# 提高造流
export LOADGEN_SCENARIO=create
export TOTAL_OPS=10000
export RATE_PER_SEC=200
export CONCURRENCY=40
export CONTENT_BYTES=400
python3 scripts/load_generate_blocks.py
```

看什么：

- `outbox_es_bulk_item_failures_total{failure_class="429"}` 上升
- `outbox_es_bulk_request_duration_seconds_*` 上升
- `outbox_lag_events` 持续增长（积压）