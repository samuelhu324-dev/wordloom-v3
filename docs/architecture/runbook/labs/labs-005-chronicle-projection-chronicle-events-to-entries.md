# Labs-005：Chronicle 投影（chronicle_events → chronicle_entries）小实验（操作指南 + 结论模板）

目标：把 Chronicle 做成“第二个标准投影闭环”。

- SoT（稳定真相）：`chronicle_events`
- Outbox（异步队列）：`chronicle_outbox_events`（方案 A：独立 outbox 表）
- 投影结果（读优化）：`chronicle_entries`
- 工程化能力：复用 outbox/worker 失败管理（lease/retry/failed/replay）

完成后沉淀为 runbook：`docs/architecture/runbook/run-004-chronicle-projection.md`

---

## 0) 前置条件

- Postgres（dev/test）
- API（能触发写 chronicle_events；或手工 SQL 注入）
- Chronicle projector worker（消费 chronicle_outbox_events，写入 chronicle_entries）
- 可选：Prometheus + Grafana

补充（与当前实现对齐）：

- outbox worker 脚本：`backend/scripts/chronicle_outbox_worker.py`
- 重建脚本（DB→DB）：`backend/scripts/rebuild_chronicle_entries.py`
- 失败重放脚本：`backend/scripts/chronicle_outbox_replay_failed.py`
- Phase C：`chronicle_events` 已提升 envelope 列（schema_version/provenance/source/actor_kind/correlation_id），仍保留 payload 兼容。

强烈建议：用 test 环境做实验（避免污染 dev 数据）。

### 0.1 Windows（PowerShell）推荐起手式（devtest-db:5435）

```powershell
cd d:\Project\wordloom-v3

./backend/scripts/devtest_db_5435_start.ps1
./backend/scripts/devtest_db_5435_migrate.ps1 -Database wordloom_test

$env:DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
```

说明：这些脚本/worker 已包含 Windows 事件循环兼容处理（psycopg async 不支持默认 Proactor loop）。

### 0.2 环境变量（示例）

> 以 WSL2 / Bash 为例（PowerShell 同理用 `$env:VAR = "..."`）。

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
export OUTBOX_MAX_BACKOFF_SECONDS=10
export OUTBOX_RECLAIM_INTERVAL_SECONDS=5
export OUTBOX_MAX_PROCESSING_SECONDS=600

# 可选：跑 N 秒后自动退出（用于实验/CI）
export OUTBOX_RUN_SECONDS=0
```

### 0.3 最小验收 SQL（手工检查）

- outbox 是否产生：
	- `select status, count(*) from chronicle_outbox_events group by 1 order by 1;`
- entries 是否物化：
	- `select count(*) from chronicle_entries;`
- 最近的 entries（按时间）：
	- `select id, event_type, book_id, block_id, actor_id, occurred_at, projection_version from chronicle_entries order by occurred_at desc limit 20;`

推荐再加 3 条（更贴近当前工程化闭环）：

- projection rebuild 状态：
	- `select * from projection_status where projection_name = 'chronicle_events_to_entries';`
- outbox → event → entry 链路抽样：
	- `select o.status, o.entity_type, o.entity_id, e.event_type, en.summary from chronicle_outbox_events o left join chronicle_events e on e.id=o.entity_id left join chronicle_entries en on en.id=o.entity_id order by o.created_at desc limit 20;`
- Phase C 列的空值率（观测是否覆盖所有写入路径）：
	- `select count(*) as total, count(*) filter (where correlation_id is null) as correlation_id_null, count(*) filter (where source is null) as source_null, count(*) filter (where actor_kind is null) as actor_kind_null from chronicle_events;`

---

## 1) 核心理念：两层测试

Chronicle 的“展示/摘要规则”会演进，所以测试必须拆层：

- A) 先确认 SoT（事件源）稳定：`chronicle_events`
- B) 再确认 Projection（读模型）符合当前规则：`chronicle_entries`

这能让你在“规则变化”时仍然工程化验收：

- 事件真相稳定：一旦写对，就像可回放的胶片。
- 投影规则可演进：像编译器输出一样，用 golden fixtures 做对照。

---

## 2) 动作上下文（Action Context）验收模板（SoT 层）

你可以把 Chronicle 理解成“审计/时间线/活动流”。它记录的不是最终状态，而是发生过的动作。

每条 `chronicle_events` 至少应具备：

- 谁做的：actor_id（可能为空，系统任务/历史数据会出现）；辅助字段 actor_kind（user/system/unknown）
- 对哪个对象：book_id（必有）+ block_id（可选）；更细的关联（tag_id 等）通常在 payload 里
- 做了什么：event_type（例如 block_updated / tag_added / book_viewed ...）
- 从什么变成什么：尽量在 payload 里放 before/after 或可还原的 diff（否则 Timeline 会“看不出发生了什么”）
- 何时：occurred_at（业务时间）+ created_at（写入时间）
- 通过什么路径写入：source（api/worker/cron/unknown）+ provenance（live/backfill/unknown）
- 关联一次动作链路（可选但强烈建议）：correlation_id（HTTP 常有；纯异步/补偿任务允许为空，不要为了过约束而伪造）

验收点：

- 字段齐不齐、actor/entity 对不对、occurred_at 是否正确。
- 写入是否遵守授权/隔离（scope：library_id / user_id 等）。
- 顺序/幂等键是否可用（event_id）。

备注：当前 `chronicle_events` 表是“最小事件存储”，**没有独立的 `request_id` 列**。如需把一次请求产生的多条事件收束为一个集合：
- 优先：使用列 `correlation_id`（Phase C 已提升为列并建立索引）
- 如果你的环境尚未迁移到 Phase C，也可以临时用 `payload->>'correlation_id'` 做聚合（代价是 JSON 扫描）
- 兜底：使用 tight time-window（例如 `created_at` 最近 2 分钟）+ `actor_id` + `book_id` 做聚合

---

## 3) 实验 1：SoT 稳定性（chronicle_events）

### 3.1 目的

确认：业务动作发生时，`chronicle_events` 写入完整且可追责。

### 3.2 步骤

1) 选择一组典型动作（建议至少覆盖）：

- rename / update / delete / restore
- 同一对象连续操作（测试 before/after 连贯性）

2) 触发动作（走 API 或 UI）。
3) 直接查询 `chronicle_events`，核对动作上下文字段。

### 3.3 预期

- `chronicle_events` 中每条记录信息完整。
- 排序稳定：按 (occurred_at, id) 做分页不会跳页/重复。

### 3.4 结论记录（填空）

- 选择的动作集合：__
- 是否满足动作上下文模板：`是/否`
- 是否满足授权/隔离：`是/否`
- 判定：SoT 稳定 `OK/FAIL`

---

## 4) 实验 2：Projection 规则（chronicle_entries）——Golden fixtures

### 4.1 目的

确认：同一批 `chronicle_events` 在当前规则下投影出的 `chronicle_entries` 是确定的、可对照的。

### 4.2 做法（推荐）

1) 准备一小批固定的 `chronicle_events`（10～50 条即可），覆盖：

- rename/update/delete/move/restore
- 同一对象连续操作（测试合并/去噪/摘要）
- 多对象交织（测试排序、分页）
- 边界：空字段、超长文本、奇怪字符

2) 执行 projector/rebuild（当前仓库已提供最终脚本）：

- 同步重建（直接写 entries）：
	- `python backend/scripts/rebuild_chronicle_entries.py --truncate`
- 或走 outbox 路径（用于验证 worker）：
	- `python backend/scripts/rebuild_chronicle_entries.py --truncate --emit-outbox`
	- 再启动 worker：`python backend/scripts/chronicle_outbox_worker.py`

当前投影的“摘要规则”是刻意保守且确定性的：summary 只拼出 `event_type + (book, block)`（见脚本实现）。
因此 golden fixtures 的断言建议从这 4 类起步：

- 1 entry per event（idempotent upsert by event id）
- occurred_at 排序稳定（按 (occurred_at, id)）
- summary 可预测（当前版本是最小摘要，不要期待富文本语义）
- payload 原样保留（用于 UI/排障；规则演进时仍可回放）

3) 断言（建议最少断言 4 类）：

- 条数
- 排序
- summary（或结构化字段）
- 关键可过滤字段（book_id / actor / day / event_type 等）

### 4.3 预期

- 产物稳定：同输入 → 同输出。
- 规则演进可控：变更后只需要更新 golden 或修 bug。

### 4.4 结论记录（填空）

- fixtures 条数：__
- golden 是否一致：`是/否`
- 判定：Projection 规则 `OK/FAIL`

---

## 5) 实验 3：规则版本化（可选但强烈建议）

如果你预计摘要/合并规则会频繁变化，建议给产物加版本字段：

- `projection_version` 或 `summary_version`

验收点：

- 新规则上线可 rebuild 产出 v2。
- 老数据仍可识别 v1（便于回滚/对比）。

---

## 6) 实验 4：时间/分页稳定性

### 6.1 目的

Chronicle 常见坑在分页/窗口：按时间排序必须稳定。

### 6.2 验收点

- 尽量使用固定 occurred_at（不要用 now），或采用“冻结时间”。
- API 分页建议用 (occurred_at, id) 作为稳定游标。
- 覆盖跨天边界（以及时区/夏令时风险，如果系统有）。

---

## 7) 实验 5：失败管理（复用 outbox worker 能力）

> 这部分的实验形状可以直接复刻 labs-004（v1–v4），但对象换成 Chronicle worker。

建议最小验收：

- transient 错误：进入 retry/backoff（pending + next_retry_at）
- deterministic 错误：直接 failed（终态）并记录 error_reason + error
- max_attempts：到顶转 failed
- replay：failed → pending（审计字段写入）

操作入口（脚本）：

- worker：`python backend/scripts/chronicle_outbox_worker.py`
- replay failed：
	- dry-run：`python backend/scripts/chronicle_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100 --dry-run`
	- 执行：`python backend/scripts/chronicle_outbox_replay_failed.py --by ops --reason "fix applied" --limit 100`

补充说明（与当前策略对齐）：

- worker 不会自动重试 `failed`（它被当作终态）；需要 ops 显式 replay 回 `pending`
- replay 会写入审计字段：last_replayed_at/last_replayed_by/last_replayed_reason/replay_count

结论记录（填空）：

- retry/backoff：`OK/FAIL`
- deterministic failed：`OK/FAIL`
- max_attempts：`OK/FAIL`
- replay 审计：`OK/FAIL`

---

## 8) 最后总结（写给未来的你）

- Chronicle 的难点不在“能不能投影”，而在“动作上下文是否可信”。
- 只要把测试拆成两层（SoT 稳定、Projection 可演进），就能工程化长期维护。
- 当你有第二个投影跑稳后，再做 DLQ/统一运维入口，收益会立刻变大。
