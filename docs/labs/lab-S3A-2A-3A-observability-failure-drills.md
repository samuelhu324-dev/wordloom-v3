# Lab-S3A/2A/3A：Observability Failure Drills（失败观测演练套件）

---

**id**: `S3A-2A-3A`
**kind**: `lab`               # log | lab | runbook | adr | note
**title**: `observability failure drills`
**status**: `draft`           # draft | stable | archived
**scope**: `S3A`
**tags**: `EVOLUTION, Observability, lab, sub/2`
**links**: ``
  **issue**: `#40`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-13`
**updated**: `2026-02-13`

---

目标：提供一组“经典失败场景菜单”，每个场景都尽量满足：

- 能稳定触发（或给出可控的触发方式）
- 能用 metrics → trace → logs 走通一条排障链
- 能验证 shared keys 三件套对齐（projection/op/batch_size/attempt/result + trace_id/span_id + correlation_id）

本 lab 是在 Labs-008 的 shared keys 约定之上扩展出来的“失败管理训练场”。

---

## 0) 前置条件

- 已完成 Labs-008（shared keys 对齐已通过验收）
- 已启动：Postgres + Elasticsearch + Jaeger（Jaeger UI `http://localhost:16686`）
- 注意：本仓库 tracing 为 opt-in（默认关闭）。若 Jaeger 查不到任何 service，优先检查 worker/API 启动日志是否出现 `event=tracing.disabled`（表示未开启）或 `event=tracing.config`（表示已开启并打印 OTLP 目标）。
- 可选：Prometheus + Grafana（用于常态化面板观测）
  - `docker compose -f docker-compose.infra.yml --profile monitoring up -d prometheus grafana`
  - Grafana `http://localhost:3000`（admin/admin）
  - Dashboard：`Wordloom • Outbox + ES Bulk`（自动 provision）

面板使用备注：应用跑在宿主机，Prometheus 在容器里抓取 `host.docker.internal:*`。
如果面板无数据，先看 `http://localhost:9090/targets` 是否 `UP`，以及 worker 是否把 `OUTBOX_METRICS_PORT` 设为 Prom 抓取的端口（常见：`9108/9109/9110/9129`）。

---

## 1) Shared Keys 口径（验收口径不重复发明）

沿用 Labs-008：

- 低基数 keys（应同时出现在 metrics labels / trace attributes / logs 字段中）：
  - `projection` / `op` / `batch_size` / `attempt` / `result`
  - （失败类）`reason`（仅 metrics labels 使用低基数枚举；细节放 logs/traces）
- 关联键：
  - logs：`trace_id` / `span_id`
  - tracing：可用 `correlation_id`（HTTP 请求链路）定位 trace

---

## 2) 执行方式（通用步骤）

每个子实验都按相同套路执行：

1) 启动 API（可选，仅用于演示 correlation_id pivot）
2) 启动单 worker（推荐先单 worker，避免多 worker 抢占导致 trace 分裂）
3) 触发/制造失败
4) 验证“证据链”三件套：
   - Metrics：用 `projection/op/reason/result` 缩小范围
   - Tracing：用 operation（例如 `projection.process_batch`）+ tags 找到 trace
   - Logs：用相同 keys + `trace_id` 取细节

最小证据集建议（按 log-S3B-2A 的快照约定存档到 `docs/labs/_snapshot/`）：
- 1 份 Jaeger trace 导出（代表性即可）
- 1 段 worker 日志截样（含 shared keys + trace_id/span_id）
- 1 次 `/metrics` 抓取（可选；通常面板即可）

---

## 2.1 面板驱动的“固定动作”（建议照抄执行）

1) Grafana 面板先缩小范围：先选 `env`，再选 `projection`（若有变量）。
2) 观察四类“主信号”（优先级从高到低）：
  - Retry：`outbox_retry_scheduled_total`（是否持续增长）
  - Failed：`outbox_failed_total` / `outbox_terminal_failed_total`
  - Lag/Age：`outbox_lag_events` / `outbox_oldest_age_seconds`
  - Stuck：`outbox_stuck_processing_events`
3) 再去 tracing：
  - 看“批处理概览”：用 operation（例如 `projection.process_batch`）+ tags（projection/op/attempt/result + `wordloom.claim_batch_id`）定位代表性 trace。
  - 精确到“单条 outbox”：用 operation=`outbox.process` + tags（`wordloom.outbox_event_id=<event_id>`）定位那条事件的 trace。
4) 最后看 logs：按同一组 shared keys 过滤，使用 `trace_id`/`span_id` 取细节（错误摘要/堆栈/实体 ID）。

PromQL 参考（用于 Prometheus Explore 或 Grafana 临时查询）：

```promql
sum by (env, projection) (rate(outbox_retry_scheduled_total{component="worker"}[1m]))
sum by (env, projection) (rate(outbox_failed_total{component="worker"}[1m]))
max by (env, projection) (outbox_lag_events{component="worker"})
max by (env, projection) (outbox_oldest_age_seconds{component="worker"})
max by (env, projection) (outbox_stuck_processing_events{component="worker"})
```

---

## 3) 经典失败场景菜单

### 3.1 实验 A：ES 挂掉 / 网络断开（最经典的 transient）

目的：验证 retry/backoff 链路是否完整、`reason` 是否收敛、shared keys 是否对齐。

触发方式（二选一）：
- 停掉 ES 容器：`docker compose -f docker-compose.infra.yml stop es`
- 或把 worker 的 ES 地址指向不可达（例如错误端口）

推荐触发（更确定）：
- 在 ES 停掉后，插入一条 `op=delete` 的 outbox 事件（即使实体不存在，也会强制走一次 ES 调用，更容易稳定触发 `es_connect` / `es_unreachable` 一类 reason）。
- 可使用辅助脚本避免 shell 引号问题：`python backend/scripts/labs/labs_009_insert_search_outbox_pending.py`（配合 `OUTBOX_OP=delete`）。

预期表现：
- Metrics：`outbox_retry_scheduled_total{projection=...,op=...,reason=...}` 增加；`outbox_failed_total` 不应立刻暴涨（除非达到 max_attempts）。
- Tracing：
  - `projection.process_batch` span 的 `result=retry`，且 `attempt` 递增；若 `result=failed`，该 span 应为 ERROR。
  - 单条事件用 `outbox.process` 的 `wordloom.outbox_event_id` 做过滤（不要用 `projection.process_batch` 去挂单条 outbox id）。
- Logs：同批次出现 `attempt=N`、错误摘要、并带 `trace_id`/`span_id`。

面板观察点（Grafana / PromQL）：

```promql
sum by (env, projection) (rate(outbox_retry_scheduled_total{component="worker"}[1m]))
sum by (env, projection) (rate(outbox_failed_total{component="worker"}[1m]))
histogram_quantile(0.95, sum by (le, env) (rate(outbox_es_bulk_request_duration_seconds_bucket{component="worker"}[5m])))
```

验收点：从 metrics 用 `projection/op/reason` 缩小范围 → 在 Jaeger 用同名 tag/operation 找到 trace → 用 trace_id 回到日志。

按按钮复现（推荐；自动落盘证据到 `docs/labs/_snapshot/auto/`）：

```bash
# 1) run：stop ES + 插入 1 条 delete outbox + bounded 跑 worker + 抓取 metrics/logs
python backend/scripts/cli.py labs run es_down_connect \
  --env-file .env.test \
  --duration 20 \
  --metrics-port 9109 \
  --op delete

# 默认落盘到：
# docs/labs/_snapshot/auto/S3A-2A-3A/es_down_connect/<run_id>/

# 2) verify：用 run 目录里抓到的 metrics-before/after 做断言
python backend/scripts/cli.py labs verify es_down_connect

# 3) export：导出 Jaeger 证据（按 outbox_event_id 精确过滤 outbox.process）
python backend/scripts/cli.py labs export es_down_connect \
  --service "wordloom-search-outbox-worker" \
  --lookback 1h \
  --limit 20

# 4) clean：恢复 ES（start es）；可选保留最近 N 次快照
python backend/scripts/cli.py labs clean es_down_connect --keep-last 10
```

Jaeger 快照导出（命令行，WSL2；输出建议落到 `docs/labs/_snapshot/`）：

```bash
# 先看有哪些 service（Jaeger 查询 traces 必须带 service 参数）
curl -sS "http://localhost:16686/api/services"

# 然后把 SERVICE 改成你实际看到的 worker service 名
SERVICE="wordloom-search-outbox-worker"
ts="$(date +%Y%m%dT%H%M%S)"
mkdir -p "docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expA"

curl -sS "http://localhost:16686/api/traces?service=${SERVICE}&lookback=1h&limit=20&operation=projection.process_batch" \
  -o "docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expA/jaeger-traces-projection_process_batch-${ts}.json"

# 精确按 outbox_event_id 导出（单条 outbox）
# 注意：这里过滤的是 operation=outbox.process，而不是 projection.process_batch。
OUTBOX_EVENT_ID="<paste-event-id>"
curl -sS \
  --data-urlencode "service=${SERVICE}" \
  --data-urlencode "lookback=1h" \
  --data-urlencode "limit=20" \
  --data-urlencode "operation=outbox.process" \
  --data-urlencode "tags={\"wordloom.outbox_event_id\":\"${OUTBOX_EVENT_ID}\"}" \
  "http://localhost:16686/api/traces" \
  -o "docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expA/jaeger-traces-outbox_process-${OUTBOX_EVENT_ID}-${ts}.json"
```

恢复：`docker compose -f docker-compose.infra.yml start es`

#### 3.1.1 本次验证结论与快照（2026-02-08）

本次在 Windows 宿主机上完成了实验 A 的端到端验证（ES stop → 插入 delete outbox → worker retry → metrics/trace/logs 取证），并确认三件套“可查询 + 可闭环”：

- Tracing：Jaeger 可用 tags 精确查询到新语义的 spans（`wordloom.outbox_event_id`、`wordloom.claim_batch_id`），且 span 自带 `wordloom.obs_schema=labs-009-v2` 用于确认运行的是新代码版本。
- Logs：worker 启动日志包含 `Observability schema: labs-009-v2 (file=...)`，并且结构化事件里写入 `claim_batch_id` / `obs_schema`。
- Metrics：`outbox_retry_scheduled_total{reason="es_connect"}` 与 `outbox_failed_total{reason="es_connect"}` 持续增长，符合“ES 网络断开 → 触发 retry/backoff”的预期。

本次快照目录：

- `docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expA/`

代表性快照文件（本次实测生成，按时间戳命名）：

- 事件 ID：`event_id-20260208T225003.txt`
- Metrics：`metrics-20260208T225003.txt`
- Worker 日志（stderr，含 schema marker 与 retry 原因）：`worker-20260208T225003.err.txt`
- Jaeger：按新 key 精确过滤 outbox：`jaeger-by-event-outbox_event_id-20260208T225249.json`
- Jaeger：按新 key 精确过滤 batch：`jaeger-projection-by-claim_batch_id-20260208T225317.json`

> 注意：本次过程中发现“同机上可能存在多个 worker 实例”的风险；建议实验期间仅保留单 worker，以免 Jaeger/metrics 被多进程污染。

#### 3.1.2 本次手测修复点回顾（manual-test/1~4）

本次实验 A 的通过，依赖以下修复点（均已落在代码与查询口径中）：

- `wordloom.outbox.id` 的语义问题：不再复用 `entity_id`，以 `wordloom.outbox_event_id` 表达 outbox 行主键；`entity_id` 单独保留为业务实体。
- batch 级 pivot：新增 `wordloom.claim_batch_id`，用于把 `projection.process_batch` 与其包含的多条 `outbox.process` 关联起来；batch span 不再绑定单条 outbox id。
- 结果聚合一致性：`projection.process_batch` 的 `result/reason/*_count` 在 `finally` 里一次性写入，且当 batch 最终失败时标记 span 为 ERROR，避免“子 span error 但 batch ok”的矛盾。
- 版本自证：新增 `wordloom.obs_schema=labs-009-v2`（spans + logs），用于快速确认 Jaeger 中的 span 来自新实现，避免“旧 worker / 未重启”导致的空查询与歧义。

#### 3.1.3 截图 1：Malfunctions 说明（手测问题复盘，manual-test/1~4）

本节对应截图 1 的 “Malfunctions” 四条问题。每条都包含：**现象**（你会看到什么）→ **根因**（为什么会这样）→ **修复**（改了什么）→ **验证**（怎么证明修好了）。

> 总原则：
> - ID 语义必须严格区分：outbox 行主键（`outbox_event_id`）≠ 业务实体（`entity_id`）。
> - batch span 只能表达 batch 级事实；单事件事实必须放在单事件 span（`outbox.process`）里。
> - “结果（result/reason）”必须是聚合后的最终结论，且写一次；不能被某个子过程覆盖。
> - Jaeger 查询必须带 `service=...`；tags key 必须与实际 span attributes 一致。

**manual-test/1 — 新标题：Batch 结果聚合错误（ok vs failed/retry）**

- 现象：
  - Jaeger 中 `projection.process_batch` 看起来 `result=ok`，但同一个 trace 里有子 span（例如 httpx `DELETE`）明确是 ERROR（ConnectError 等）。
  - 排障链断裂：从 batch span 看不到“这是一次 retry/failed”，必须下钻子 span 才知道出错，且容易误判为“整体成功”。
- 根因：
  - batch 的 `result` / `reason` 被“局部流程”过早写入，或者在多事件/多分支路径下被覆盖，最后没有在“收尾阶段”统一决策。
  - 结果字段缺少严格的聚合策略（ok/retry/failed 的优先级与计数），导致 batch 语义不稳定。
- 修复：
  - 在 batch 处理末尾（`finally`）**一次性**写入 `result`、`reason`、`ok_count/retry_count/failed_count`，用聚合后的最终结论落地。
  - 当 batch 最终为 `failed` 时，将 batch span 标为 ERROR，避免“子 span error 但 batch ok”的矛盾。
- 验证（以实验 A 为例，ES down）：
  - 预期 `projection.process_batch` 的 tags 至少包含：`result="retry"`、`reason="es_connect"`、`retry_count=1`（对于 batch_size=1 的场景）。
  - 对应快照：`jaeger-projection-by-claim_batch_id-20260208T225317.json`。

**manual-test/2 — 新标题：Outbox 事件 ID 写错（event_id vs entity_id）**

- 现象：
  - span attribute 里用于查询 outbox 的 ID（旧 key：`wordloom.outbox.id`）实际上等于 `entity_id`，导致你拿着“真实 outbox 行 id”去 Jaeger 按 tags 查询时，结果为空。
  - 后果是无法完成“按 outbox_event_id 精确定位单条事件”的标准排障动作。
- 根因：
  - outbox 插入脚本/构造逻辑复用了同一个 UUID 同时作为 outbox 行主键与业务实体 ID，或者把 entity_id 塞进了 outbox id 的标签。
  - 语义上把“业务实体”与“事件载体（outbox row）”混为一谈。
- 修复：
  - 明确用 `wordloom.outbox_event_id` 表达 outbox 行主键；`wordloom.entity_id` 单独表达业务实体。
  - 插入辅助脚本生成**不同的** outbox_event_id 与 entity_id，并支持显式指定 entity_id（用于可重复实验）。
- 验证：
  - 从快照文件 `event_id-20260208T225003.txt` 取出 OUTBOX_EVENT_ID，用 `operation=outbox.process` + `tags={"wordloom.outbox_event_id":"..."}` 查询，必须能命中。
  - 对应快照：`jaeger-by-event-outbox_event_id-20260208T225249.json`。

**manual-test/3 — 新标题：Jaeger tags 查不到（key 漂移 / 运行旧代码 / 未重启）**

- 现象：
  - 你确认 Jaeger 里“有 trace”，但按文档给的 tags（例如 `wordloom.outbox_event_id`、`wordloom.claim_batch_id`）查询返回空，误以为“span 没上报/丢了”。
  - 或者 Jaeger 导出里仍出现旧字段（`wordloom.outbox.id`、`wordloom.entity.id`），与新文档/新查询口径不一致。
- 根因（通常是组合拳）：
  - worker 进程仍在跑旧代码（或未重启），导致 span attributes 仍是旧 key；你用新 key 去查自然为空。
  - 同机多个 worker 同时在跑，service/operation/tags 混杂，造成“看起来有，但你查不到你想要的那条”。
  - Jaeger API 查询忘了带 `service=...`（Jaeger 的 `/api/traces` 必须带 service 才能查），或 tags JSON 没有正确 URL encode。
- 修复：
  - 增加 schema 自证字段：所有关键 spans/logs 都带 `wordloom.obs_schema=labs-009-v2`，并在启动日志输出 `Observability schema: labs-009-v2 (file=...)`，用来一眼识别“这是不是新 worker”。
  - 文档查询口径统一：推荐在 tags 里同时加 `wordloom.obs_schema`（尤其是在你怀疑有旧进程污染时）。
- 验证：
  - 在 worker 日志中必须能看到 schema 启动行（见 `worker-20260208T225003.err.txt`）。
  - 在 Jaeger 导出中必须能看到 `wordloom.obs_schema=labs-009-v2` 且 tags key 为 `wordloom.outbox_event_id` / `wordloom.claim_batch_id`。

**manual-test/4 — 新标题：操作名/服务名混淆（旧 outbox.process vs 新 worker spans）**

- 现象：
  - 你在 Jaeger UI/API 里用错误的 operation 名称（例如用 `projection.process_batch` 去挂单事件筛选，或 service 选错），导致导出结果为空或误导。
  - “旧 outbox.process 的概念”与“新 worker 的 operation/attributes 结构”混在一起，导致排障路径不确定。
- 根因：
  - 从旧实现/旧命名迁移到新 worker 后，查询动作没有同步更新：
    - 单事件应使用 `operation=outbox.process`（并用 `wordloom.outbox_event_id` 过滤）。
    - 批处理概览应使用 `operation=projection.process_batch`（并用 `wordloom.claim_batch_id` 过滤）。
  - 或者 Jaeger 中存在多个 service（多 worker/多组件），没有先确认 “service 列表与 operations 列表”。
- 修复：
  - 文档明确规定两条 pivot 路径：
    - “单条 outbox”：`outbox.process` + `wordloom.outbox_event_id`。
    - “批处理概览”：`projection.process_batch` + `wordloom.claim_batch_id`。
  - 先查 `GET /api/services` 与 `GET /api/services/<service>/operations`，确认 service 与 operation 名称再做 traces 查询。
- 验证：
  - 先看 services 快照确认 service 名：`jaeger-services-20260208T225003.json`。
  - 再看 operations 快照确认 operation 列表：`jaeger-operations-20260208T225003.json`。

---

### 3.2 实验 B：ES 429（限流/背压：最像真实生产）

目的：验证“可恢复错误分类”正确（429 → retry/backoff），以及 `reason` 的低基数设计（例如统一为 `rate_limited`）。

触发方式（两种模式，建议先做“可控注入”，再做一次轻量压测）：

1) 可控注入 429（更稳定，强信号，10 分钟级别跑完）

- 思路：在系统内侧注入 429，让输出更干净，便于严格断言 “429 => retry/backoff”。
- 本仓库当前实现：search worker 已内置实验开关（默认关闭），在单事件路径上注入 `httpx.HTTPStatusError(429)`。
- 建议配置（WSL2 / bash 示例）：

```bash
# 只对 upsert/delete 注入 429（每 3 次注入 1 次），并固定随机种子
export OUTBOX_EXPERIMENT_ES_429_EVERY_N=3
export OUTBOX_EXPERIMENT_ES_429_OPS=upsert,delete
export OUTBOX_EXPERIMENT_ES_429_SEED=1

# 建议先用非 bulk 路径（更直观）；bulk 相关指标可在实验 D/压测阶段再覆盖
export OUTBOX_USE_ES_BULK=0
```

> 说明：本 worker 当前对 429 的低基数 reason 命名为 `es_429`（可视为 “rate_limited” 的实现名）。验收关注低基数与可枚举性；若未来重命名为 `rate_limited`，需要同步更新 metrics/traces/logs 与文档。

2) 压测逼出 429（更像真实生产，但不保证稳定复现）

- 思路：提高 batch_size/并发，或降低 ES 资源，把系统推到背压点，观察 429 的真实分布以及 backoff/jitter 是否真在降压。
- 风险：会夹杂 timeout/5xx/连接池耗尽等噪声，不适合做“分类逻辑”的严格断言。

预期表现：
- Metrics：`reason` 收敛成低基数枚举（当前实现：`reason="es_429"`）；不要把具体错误串塞 label。
- Tracing：`result=retry`，并能看到 batch_size/op/attempt 维度。
- Logs：记录 429 细节（状态码、响应体摘要），同时 `reason=rate_limited`。

验收建议（最小证据集）：
- 1 张 Prometheus/Grafana 证据：`outbox_retry_scheduled_total{reason="es_429"}` 持续增长
- 1 份 Jaeger trace：`projection.process_batch` 显示 `result=retry`，并能下钻看到触发 retry 的事件 span
- 1 段 logs：包含 status=429（或错误摘要）+ shared keys + `trace_id/span_id`

#### 3.2.0 本次验证结论与快照（2026-02-13）

结论：**实验 B 的 429 注入已经跑通**。

- 注入证据（强信号）：worker 单事件处理路径会出现 `Injected 429 (fault injection)`（`httpx.HTTPStatusError`，status=429）。
- 解释口径（避免误读）：当使用 `OUTBOX_EXPERIMENT_ES_429_EVERY_N` 时，注入模式为 **every_n**，有效注入概率约为 $1/n$；启动日志会输出 `mode=every_n` 与 `effective_ratio`（例如 every_n=3 时约为 0.333），不再出现“ratio=0.00 但仍在注入”的误导。
- Tracing/Jaeger（本节先不展开）：若 Jaeger 仍为空，优先把它当作“tracing 未开启或 exporter 未配置”的独立问题处理，不影响“注入是否生效”的结论。

建议快照（落到 `docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expB/`）：
- 1 段 worker 日志：包含 `ES 429 fault injection enabled: mode=... effective_ratio=...` + `Injected 429`
- 1 次 metrics 抓取（可选）：确认 retry/backoff 指标在增长

#### 3.2.0.1 本次压力测试结果（2026-02-14）：失败

结论：**本次“压测逼出真实 429”未能稳定复现**。

- 现象（两极分化）：
  - 要么系统整体非常稳定：ES 线程池 `rejected` 维持为 0，worker 侧也没有出现可用于验收的 `429 → retry/backoff` 证据链。
  - 要么 ES 在更激进的压力下直接失稳/重启（连接 reset/refused），导致在“达到背压点并返回 429”之前就先不可用了。
- 结论口径：真实生产里 429（背压/限流）是否出现、以什么形态出现，受资源与负载形态影响很大；在本地/实验环境里很难用“纯压测”获得**稳定、可复验**的 429 样本。
- 推荐策略：
  - **分类逻辑/可恢复性验证（本实验 B 的主目标）优先使用“可控注入 429”**：信号干净、断言明确、可重复。
  - “压测逼出 429”建议降级为探索性验证：用于观察系统在高负载下的整体行为（吞吐/积压/超时/重启边界），不作为必过验收项。

#### 3.2.1 本次 Malfunctions（manual-test/1：tracing 未开启 / OTLP 协议端口不匹配）

> 这段对应“实验 B 已打出 metrics/logs，但 Jaeger 导出为空”的问题复盘。
> 写法沿用截图 1：**现象** → **根因** → **修补** → **验证**。

- 现象：
  - `GET http://localhost:16686/api/services` 返回 `data=null` 或 `data=[]`；进一步按 outbox_event_id/tags 查询 traces 也为空。
  - 同时，worker 的 metrics/logs 明明已经出现 `reason="es_429"` 的失败与 retry 证据链（说明实验 B 注入本身生效）。
  - 常见伴随信号：worker 日志里没有 `trace_id/span_id` 字段（几乎可以直接判定 tracing 没有开启）。

- 根因：
  - tracing 在本仓库是 **opt-in**（默认关闭）。如果没有设置 `WORDLOOM_TRACING_ENABLED=1`（或被 `OTEL_SDK_DISABLED=true` 关闭），那么 worker/API 不会发任何 spans，Jaeger 就会“完全空”。
  - 另一个高频踩坑是 **OTLP 协议/端口不匹配**：
    - `4317` 是 OTLP gRPC；`4318` 是 OTLP HTTP。
  - PowerShell 里 `curl` 常是 `Invoke-WebRequest` 的别名，输出/参数行为与 WSL/bash 的 curl 不一致，容易误判“服务不可达”。

- 验证（建议作为实验 B 的硬前置/硬验收动作）：
  - 先确认 Jaeger 本体可用（PowerShell）：

    ```powershell
    (Invoke-RestMethod -Uri "http://localhost:16686/api/services" -Method Get) | ConvertTo-Json -Depth 5
    ```

  - 然后启动 worker 并触发一次实验 B（429 注入），再检查 services：
    - services 的 `data` 必须包含 `wordloom-search-outbox-worker`（或你设置的 `OTEL_SERVICE_NAME`）。
    - worker 启动日志必须出现 `event=tracing.config`（而不是 `tracing.disabled`）。

#### 3.2.2 本次 Malfunctions（manual-test/2：span tags + ratio/effective mode 打印误导）

> 这段对应截图 1 的 `manual-test/2: span + ratio computation`。

- 现象：
  - 注入使用 `OUTBOX_EXPERIMENT_ES_429_EVERY_N=3` 已经稳定生效，但启动日志仍显示 `ratio=0.00`，容易让读者误判“没有开启注入”。
  - Jaeger 里用 `wordloom.outbox_event_id` 查 `operation=outbox.process` 返回空时，很难区分是“span 没有该 tag”还是“tracing 根本没启用/没导出”。

- 根因：
  - 注入逻辑支持两种模式：`ratio`（随机）与 `every_n`（确定性）。当 `every_n` 生效时，`ratio` 允许为 0；但日志只打印了 `ratio`，没有打印“生效模式”。
  - span 关联键如果不够显式（例如缺少 outbox_event_id、注入配置、是否 injected），会导致“证据链”不稳：你无法在 trace 中一键定位到“这次 429 是被注入的”。

- 修补：
  - 启动日志改为打印 `mode` + `effective_ratio`（并保留原始 `ratio/every_n/ops/seed`），明确“当前到底按哪个模式在注入”。
  - `operation=outbox.process` span 增强 attributes：确保 `wordloom.outbox_event_id` 存在，并补充 `wordloom.labs.es_429.*`（mode/ratio/every_n/ops/seed）；当实际发生注入时额外打 `wordloom.labs.es_429.injected=true` 与计数器等。
  - tracing 启动增加一次性结构化日志 `event=tracing.startup`：明确 enabled/otlp_target/collector_reachable/exporter_configured，用于快速判断“为什么 Jaeger 为空”。

- 验证：
  - 启动 worker 时应出现类似日志：`ES 429 fault injection enabled: mode=every_n effective_ratio=0.333 ...`。
  - 若 tracing 已开启且 exporter 已配置，Jaeger 查询可优先用：
    - `operation=outbox.process` + `tags={"wordloom.outbox_event_id":"<id>"}`
    - 或 `tags={"wordloom.labs.es_429.injected":true}`（筛出确实被注入的 span）。

面板观察点（Grafana / PromQL）：

```promql
sum by (env, projection, reason) (rate(outbox_retry_scheduled_total{component="worker"}[1m]))
sum by (env) (rate(outbox_es_bulk_item_failures_total{component="worker", failure_class="429"}[1m]))
```

验收点：能清晰区分 429（可恢复）与 4xx（不可恢复，见实验 C）。

Jaeger 快照导出（推荐用统一入口，避免 tags URL 编码/PowerShell `curl` 别名踩坑）：

```bash
python backend/scripts/cli.py labs export-jaeger \
  --service "wordloom-search-outbox-worker" \
  --lookback 1h \
  --limit 20

# outputs default to:
# docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expB/<run_id>/_exports/
```

---

### 3.3 实验 C：确定性 4xx（毒丸数据：应直接 failed）

目的：验证 deterministic failure 不要无限重试；这类应进入 failed/DLQ 与人工修复路径。

触发方式（按钮化，推荐）：对目标 ES index 开启写入阻断（`index.blocks.write=true`），让 worker 写 ES 时稳定得到 4xx（reason=`es_4xx`），从而进入 `failed` 而不是 retry。

按按钮复现（WSL2 / bash；默认读取 repo 根目录 `.env.test`）：

```bash
# 1) run：开启 write block + 插入 1 条 outbox + bounded 跑 worker + 抓取 metrics/logs
python backend/scripts/cli.py labs run es_write_block_4xx \
  --env-file .env.test \
  --duration 20 \
  --metrics-port 9109

# 输出会打印 outdir（run 目录）。默认落盘到：
# docs/labs/_snapshot/auto/S3A-2A-3A/es_write_block_4xx/<run_id>/

# 2) verify：用 run 目录里抓到的 metrics-before/after 做断言
python backend/scripts/cli.py labs verify es_write_block_4xx

# 3) export：导出 Jaeger 证据（按 outbox_event_id 精确过滤 outbox.process）
python backend/scripts/cli.py labs export es_write_block_4xx \
  --service "wordloom-search-outbox-worker" \
  --lookback 1h \
  --limit 20

# 4) clean：关闭 write block（恢复 ES 可写）；可选保留最近 N 次快照
python backend/scripts/cli.py labs clean es_write_block_4xx --env-file .env.test --keep-last 10
```

预期表现：
- Metrics：`outbox_failed_total{reason=...}` 增加；`outbox_retry_scheduled_total` 不应增加。
- Tracing：`result=failed`，并带 error 信息（细节仍放 logs）。
- Logs：落 `error_reason` / error 摘要（堆栈在 logs，不进 metrics label）。

面板观察点（Grafana / PromQL）：

```promql
sum by (env, projection) (rate(outbox_failed_total{component="worker"}[1m]))
sum by (env, projection) (rate(outbox_terminal_failed_total{component="worker"}[1m]))
```

验收点：failed 记录能被 replay/人工处理流程捞出（失败管理闭环）。

最小证据集（自动快照目录下应能找到）：

- `_recipe.json`：本次注入与运行参数（不包含敏感 env）
- `_metrics/metrics-before.txt` + `_metrics/metrics-after.txt`（verify 断言来源）
- `_logs/worker-<run_id>.log`（含 shared keys + trace_id/span_id）
- `_exports/`：Jaeger 导出（export 后生成）

---

### 3.4 实验 D：部分成功（partial bulk success）

目的：验证结果语义能表达“部分成功”，而不是只有 ok/failed。

触发方式：同一批次混入一条确定会失败的事件（毒丸）+ 其他正常事件。

预期表现：
- Metrics：要么 `result="partial"`，要么用 `processed_total + failed_total` 组合表达（更常见）。
- Tracing：`result=partial`，并在 span attributes 写入 `success_count` / `failure_count`。
- Logs：记录失败的 entity_id/event_id 列表（仅 logs/traces）。

面板观察点（Grafana / PromQL）：

```promql
sum by (env, projection) (rate(outbox_processed_total{component="worker"}[1m]))
sum by (env, projection) (rate(outbox_failed_total{component="worker"}[1m]))
sum by (env, result) (rate(outbox_es_bulk_requests_total{component="worker"}[1m]))
```

验收点：验证“低基数 keys + 高信息细节”分层合理。

按按钮复现（推荐；自动落盘证据到 `docs/labs/_snapshot/auto/`）：

```bash
# 1) run：强制走 ES bulk + 注入“部分失败”的 bulk 响应（partial）+ 插入 2 条 outbox
python backend/scripts/cli.py labs run es_bulk_partial \
  --env-file .env.test \
  --duration 25 \
  --metrics-port 9125 \
  --scrape-delay 2 \
  --trigger-count 2 \
  --bulk-size 10 \
  --partial-status 400

# 默认落盘到：
# docs/labs/_snapshot/auto/S3A-2A-3A/es_bulk_partial/<run_id>/

# 2) verify：断言 bulk partial + item success/failed 等指标增量
python backend/scripts/cli.py labs verify es_bulk_partial

# 3) export：导出 Jaeger 证据（bulk 模式可能没有 per-event outbox.process，因此默认按 obs_schema 收敛导出）
python backend/scripts/cli.py labs export es_bulk_partial \
  --service "wordloom-search-outbox-worker" \
  --lookback 30m \
  --limit 50

# 4) clean：本实验为 env 注入（无需恢复外部状态）；可选保留最近 N 次快照
python backend/scripts/cli.py labs clean es_bulk_partial --keep-last 10
```

---

### 3.5 实验 E：DB 竞争/锁/死锁（worker 自身的现实主义）

目的：验证 claim_batch / lease / reclaim 相关链路的可观测性，尤其多 worker 并发时。

触发方式：
- 同时启动两个 worker 抢同一 outbox 表。
- 或在 DB 手动持锁制造超时。

预期表现：
- Metrics：出现 claim 冲突/超时相关指标或 `reason=db_contention`。
- Tracing：若有 `outbox.claim_batch` / db 子 span，会非常直观。
- Logs：出现 claim 成功/失败的结构化事件（例如 claimed=0 也是重要信号）。

面板观察点（Grafana / PromQL）：

```promql
max by (env, projection) (outbox_inflight_events{component="worker"})
max by (env, projection) (outbox_oldest_age_seconds{component="worker"})
max by (env, projection) (outbox_lag_events{component="worker"})
```

验收点：能回答“吞吐下降卡在 claim 还是卡在处理”。

按按钮复现（推荐；自动落盘证据到 `docs/labs/_snapshot/auto/`）：

```bash
# 1) run：启动两个 worker（不同 metrics 端口）并开启“非原子 claim”注入，制造 claim 竞争/owner mismatch 信号
python backend/scripts/cli.py labs run db_claim_contention \
  --env-file .env.test \
  --duration 25 \
  --metrics-port-1 9126 \
  --metrics-port-2 9127 \
  --scrape-delay 2 \
  --trigger-count 1 \
  --op upsert \
  --break-claim-sleep 1.0

# 默认落盘到：
# docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/<run_id>/

# 2) verify：断言 owner_mismatch_skips_total + processed_total 的增量
python backend/scripts/cli.py labs verify db_claim_contention

# 3) export：导出 Jaeger 证据（优先按 claim_batch_id；否则 fallback 按 obs_schema 收敛导出）
python backend/scripts/cli.py labs export db_claim_contention \
  --service "wordloom-search-outbox-worker" \
  --lookback 30m \
  --limit 50

# 4) clean：本实验为 env 注入（无需恢复外部状态）；可选保留最近 N 次快照
python backend/scripts/cli.py labs clean db_claim_contention --keep-last 10
```

#### 3.5.1 本次验证结论与快照（2026-02-14）

结论：**实验 E（DB claim 竞争 / owner mismatch 注入）已完成端到端验证**（run → verify → export → clean），并确认在双 worker 并发下仍能通过 metrics → traces → logs 闭环取证。

本次使用的代表性 run：

- `run_id=20260214T164207`
- 自动快照目录：`docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/20260214T164207/`

证据链要点：

- Metrics：`outbox_owner_mismatch_skips_total` 出现可观测增量（体现 claim 竞争/抢占），同时 `outbox_processed_total` 增长，且本次未引入非预期 `outbox_failed_total` 增量（verify 通过）。
- Tracing/Jaeger：已导出 `operation=outbox.claim_batch` 的 traces（按 `wordloom.obs_schema=labs-009-v2` 收敛，避免被同机其他进程污染），代表性导出文件：
  - `docs/labs/_snapshot/auto/S3A-2A-3A/db_claim_contention/20260214T164207/_exports/jaeger-traces-tags-20260214T084651.json`
  - 本次导出结果：返回 traces 数量为 50
- Logs：快照目录 `_logs/` 下包含双 worker 的运行日志，且能以 trace_id/span_id 回跳定位到对应 claim/处理路径。

备注（导出可信度）：Jaeger API 的 metadata 有时会出现 `limit=0/total=0` 但实际 `data` 非空的情况；以导出 JSON 内 `data` 数组是否非空为准。

---

### 3.6 实验 F：stuck & reclaim（租约过期回收）

目的：验证自愈路径（卡住 → 过期 → reclaim）是否可观测；并验证 tracing 缺失时仍能靠 metrics+logs 取证。

触发方式（任选其一）：
- 在处理逻辑里人为 sleep（让处理时间超过 lease/TTL）。
- 或 kill worker（模拟崩溃），等待下一轮 reclaim。

预期表现：
- Metrics：stuck/reclaimed 相关计数增加（若已有指标）。
- Tracing：可能断掉（进程死了）——这是预期，用来证明 tracing 非万能。
- Logs：必须有“强制回收”的审计字段（who/when/why）。

验收点：trace 缺失时仍能从 metrics+logs 复盘。

#### 3.6.1 本次验证结论与快照（2026-02-14）

本次结论：实验 F 的“卡住 → 租约过期 → reclaim → 继续处理”自愈路径已可观测且可按钮化复现。

本次 run_id：`20260214T171226`

快照路径：

- `docs/labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/20260214T171226/`
  - `_logs/worker1-20260214T171226.log`：worker1 在 claim 后被 controller kill（模拟崩溃/卡住）。
  - `_logs/worker2-20260214T171226.log`：出现 reclaim 日志（例如 `Reclaimed 5 stuck outbox events ...`），并继续完成处理（可见 `Outbox upsert:` 处理日志）。
  - `_metrics/metrics-before-2.txt`、`_metrics/metrics-after-2.txt`：Prometheus 快照（本次 verify 允许“metrics delta=0 但 logs 已取证”的情况，避免采样时序导致误判）。
  - `_result.json`：verify 结果（OK）。

Tracing/Jaeger：已导出 `operation=outbox.claim_batch` 的 traces（按 `wordloom.obs_schema=labs-009-v2` 收敛），代表性导出文件：

- `docs/labs/_snapshot/auto/S3A-2A-3A/stuck_reclaim/20260214T171226/_exports/jaeger-traces-tags-20260214T091956.json`
  - 本次导出结果：返回 traces 数量为 120

---

### 3.7 实验 G：重复投递 / 幂等（at-least-once 的必修课）

目的：验证重复事件不会造成重复副作用，并把“去重命中/noop”变成可观测。

触发方式：复制同一个 outbox event（同 event_id 或同语义）多次。

预期表现：
- Metrics：`dedupe_hit_total` 或 `idempotent_noop_total` 增加（若已有指标）。
- Tracing：span attribute `deduped=true` / `noop=true`。
- Logs：记录跳过原因（duplicate key / already applied）。

验收点：能解释“吞吐看似正常但实际没有写入”的情况。

#### 3.7.1 本次验证结论与快照（2026-02-14）

结论：**实验 G（重复投递 / 幂等 noop）已完成端到端验证**（run → verify → export → clean）。本次用“同一实体的重复 delete”来模拟 at-least-once 重复投递：第一次 delete 生效，第二次 delete 在 ES 返回 404 时被视为安全 noop，并能被 metrics / traces / logs 取证。

本次使用的代表性 run：

- `run_id=20260214T173415`
- 自动快照目录：`docs/labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/20260214T173415/`

证据链要点：

- Metrics：新增并验证 `outbox_idempotent_noop_total{projection="search_index_to_elastic",op="delete",reason="es_404"}` 有增量（体现“重复 delete → 404 noop”），同时 `outbox_failed_total` 无异常增量（verify 通过）。
- Logs：worker 日志出现明确 noop 语句：`Outbox delete: doc <...> not found in ES (noop)`（对应第二次重复 delete）。
- Tracing/Jaeger：已导出 `operation=outbox.process` 的 traces（按 `wordloom.obs_schema=labs-009-v2` + `wordloom.entity_id=<entity_id>` 收敛），代表性导出文件：
  - `docs/labs/_snapshot/auto/S3A-2A-3A/duplicate_delivery/20260214T173415/_exports/jaeger-traces-tags-20260214T093452.json`

---

### 3.8 实验 H：投影规则版本化风险（projection_version）

目的：把规则版本化从“概念”变成“可观测现实”。

触发方式：切换投影版本（例如 `CHRONICLE_PROJECTION_VERSION`），让同一批输入走 v1/v2。

预期表现：
- Tracing：span 带 `projection_version=1/2`。
- Logs：同字段可过滤。
- Metrics：一般不建议把 version 放 label（会涨维）；可以把版本放 logs/traces 或把版本并入 projection 名称。

验收点：能快速回答“异常来自 v1 还是 v2”。

#### 3.8.1 本次验证结论与快照（2026-02-14）

结论：**实验 H（projection_version）已完成端到端自动化验证**（run → verify → export）。同一条 `chronicle_event` 被重复 enqueue 两次，分别在 `CHRONICLE_PROJECTION_VERSION=1` 与 `CHRONICLE_PROJECTION_VERSION=2` 下处理，最终 `chronicle_entries.projection_version` 可被 DB probe 明确取证为 1→2 的变化。

本次使用的代表性 run：

- `run_id=20260214T175011`
- 自动快照目录：`docs/labs/_snapshot/auto/S3A-2A-3A/projection_version/20260214T175011/`

证据链要点：

- DB Probe：
  - `_probe_entry_v1.json`：`projection_version=1`
  - `_probe_entry_v2.json`：`projection_version=2`
- Logs：
  - `_logs/worker-v1-20260214T175011.log`：v1 worker 处理日志
  - `_logs/worker-v2-20260214T175011.log`：v2 worker 处理日志
- Tracing/Jaeger：已导出 `operation=outbox.process` 的 traces（按 `wordloom.entity.id=<chronicle_event_id>` 收敛），代表性导出文件：
  - `docs/labs/_snapshot/auto/S3A-2A-3A/projection_version/20260214T175011/_exports/jaeger-traces-tags-20260214T095135.json`
