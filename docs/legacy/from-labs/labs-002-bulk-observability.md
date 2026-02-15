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

### B 的“预期效果”总结（可直接写进实验结论）

把突发拆成两个阶段分别看（避免被“总体平均值”误导）：

- Produced/s：写入侧是否吞吐（API 每秒产生多少 outbox）
- Processed/s：事件是否吞吐（worker 每秒处理多少 outbox）
- Net rate：是否在“追平积压”（$\text{Processed/s} - \text{Produced/s}$）
- Lag：积压是否上升/回落（`outbox_lag_events`）
- Bulk p95：单次 bulk 的耗时（健康度）
- 429 ratio：ES 吃不下的信号（`failure_class="429"` 的占比）
- Items/s：真实写入吞吐（`outbox_es_bulk_items_total{result="success"}` 的 rate）

你会看到一个很典型的 tradeoff：bulk p95 ↑（单次请求更慢）并不必然导致 Processed/s ↓，因为一次 bulk 能带很多 items。

低速阶段（基线 / 预热）：

- 预期：Produced/s ≈ Processed/s，Net rate ≈ 0，Lag ≈ 0（或稳定在很小范围）
- Bulk p95：相对稳定；429 ratio/failed：≈ 0

突发阶段（冲击 / 瞬时过载）：

- 预期：Produced/s 阶跃上升；若超过处理能力则 Net rate < 0 且 Lag 上升
- 突发结束后：若 worker+ES 有余量，Net rate > 0（清债）且 Lag 回落
- 若进一步加压：Bulk p95 抬升，并可能出现 429 ratio 上升（进入需要 backoff/降档的区间）

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

### C 的实验结果记录（截图1）

从截图1能读到的总体状态：

- worker failed/s 仍然为 0
- bulk request 的 result 几乎全是 success（partial/failed 基本为 0）
- 429 ratio 为 0
- bulk items/s 在 burst 时能爬到 50+ ops/s（success）
- `outbox_lag_events` 有 spike，但没有“持续单边上升成坡”

判读：这更像系统在健康区间内的“批处理抖动 + 热 key 造成的短暂不稳定”，不是过载。

真正需要判定为“异常/过载”的典型画像：

- Net rate 长时间 < 0（持续欠债，追不回来）
- `outbox_lag_events` 持续上升（越堆越多）
- bulk p95/p99 持续抬升，且抖动带宽开始扩大
- 429 或 partial/failed 开始出现并上升

结论（截图1）：更像“训练后肌肉酸但没受伤”。

---

## 5) 工况 D：delete（清理/回收）

目的：覆盖 delete item（payload 更小、语义不同）。脚本把 404 当作幂等成功。

```bash
export LOADGEN_SCENARIO=create_then_delete
export POOL_SIZE=2000
export TOTAL_OPS=2000

python3 scripts/load_generate_blocks.py
```

### D 的实验结论（总体诊断）

一句话总结：工况 D 表现正常，系统健康，delete 相位滞后会让图形呈现“两段式”（先 upsert 后 delete）。

你可以给它贴上这些标签：

- ES 健康：p95 稳，429=0，bulk 结果全 success
- worker 正常：failed=0，processed 有明显 upsert→delete 的阶段性
- 积压可控：lag 只有瞬时 spike，没有持续抬升
- net rate 抖：主要是窗口/相位差导致的“差分噪声”，不是实质性欠债

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

### E 的实验结论（总体诊断）

正常。这个实验 E 更像是在验证：

- mixed 业务形态下，bulk 路径没有把系统搞炸
- 指标体系能把“请求级 vs item 级”分开看清楚（bulk request 成功/耗时 vs item failures/items/s）

它不是那种把 ES/worker 打到临界点的压测。要更像生产里的“难看时刻”，通常需要叠加更多毒性因素，比如：

- 更大的 payload（把 `CONTENT_BYTES` 拉上去）
- 更高并发 + 更短 scrape/窗口（让观测更敏感）
- update 热点更集中（`HOTSET_SIZE` 更小）
- 故意把 bulk size 调大 / flush 频率调低，让批处理更“块状”，lag 会更明显

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