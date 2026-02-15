# Log-S2C-1A-1A：实验 B（ES 429）把“野生手测”改造成“可重复实验装置”（平台化前置版）

Status: draft
links:
- Labs-009：`docs/architecture/runbook/labs/labs-009-observability-failure-drills.md`
- 对照日志（结构模板）：`docs/logs/logs/v2-logs/log-S2C-1A-labs-009-expB.md`
- Jaeger 导出脚本：`backend/scripts/labs/labs_009_export_jaeger.py`
- Outbox worker：`backend/scripts/search_outbox_worker.py`

## Background

失败注入在真实系统里经常“不像测试那样听话”：环境、时序、队列供给、观测链路一致性（metrics/trace/logs）、以及外部依赖（ES/Jaeger/OTLP 协议）都会叠加出大量变量。
因此这份 log 的目标不是“让 Copilot 更聪明”，而是把实验从“手工玄学”变成“可重复的实验装置”：先最小化、可控化、确定性化，再升级到更真实的压测式触发；平台按钮化属于后期工作。

## What/How to do

### 1) 原则：先可重复，再真实

draft:
- 先不要上来就做“压测式 429”。压测式会引入很多噪声变量：队列空/`claimed=0`、连接复用、bulk 幂等、重试策略差异、OTLP 协议/端口不匹配、Jaeger 查询元数据异常、shared keys 漂移等。
- 优先跑“确定性注入（fault-injection）”做最小可复现：用 100% 命中、单条事件、单 worker、短时间窗口，把链路对齐。
- 定位顺序：先把“系统行为正确且可观测”跑通，再用压测验证“像生产”。

adopted:

### 2) 触发策略对比：压测触发 vs adapter 注入

draft:
- 模式 A：压测触发（系统外侧触发）
	- 做法：提高 batch_size/并发，或降低 ES 资源，逼出真实的 429。
	- 优点：更接近生产真实性。
	- 缺点：复现不稳定；容易夹杂 timeout/5xx/连接池耗尽等多类失败，断言困难。
- 模式 B：adapter 注入（系统内侧触发）
	- 做法：在适配层对指定 op/节奏确定性抛出 429（最好“只打一次”或“每 N 次一次”）。
	- 优点：强信号、复现稳定、断言干净；适合前期把“分类 + 证据链”校准好。
	- 缺点：不制造真实资源竞争，不验证系统在资源紧张下的回稳能力。

adopted:

### 3) “三开关”实验装置：Fault / Obs / Fixture（每次只动一个）

draft:
- 开关 1：注入开关（Fault）
	- 目标：让失败“确定发生”，并可控（例如：100% 命中、只打一次、绑定某个 outbox_event）。
	- 示例形态：`FAULTS_ENABLED=1`、`FAULT_RULE=es_429_once`（或等价 env knobs）。
- 开关 2：观测开关（Obs）
	- 目标：shared keys 必须写全，并且“写不出来就 fail fast”。
	- 需要强制齐全的字段（示例）：`correlation_id`、`wordloom.outbox_event_id`、`projection`、`op`、`attempt`、`result`、`reason`。
- 开关 3：数据开关（Fixture）
	- 目标：固定输入与节奏，避免测到“空气”。
	- 做法：固定 outbox 事件数量（≤10）、固定 worker 数量（1）、固定 batch_size（先 1 后 5）、固定时间语义（避免所有东西都依赖 now）。

adopted:

### 4) 系统不变量 → 验收清单（把“感觉正确”变成“断言正确”）

draft:
- 不变量 1：同一条 outbox_event 必须能用同一个 key 串起 logs / metrics / trace。
	- 主 key：`wordloom.outbox_event_id`（字段名必须统一）。
- 不变量 2：`result` 不允许“看起来 ok，但实际 error=true”。
	- 规则：只要任意关键子步骤失败（或 span `error=true`），聚合/父 span 的 `result` 不能是 `ok`。
- 不变量 3：429 必须归类为可恢复（transient）。
	- 规则：进入 retry/backoff；写低基数 `reason`（例如 `rate_limited` / `es_429`）；产生 `next_retry_at`。
- 不变量 4：非 429 的确定性 4xx 必须归类为不可恢复。
	- 规则：直接 failed + error_reason（避免无限 retry）。
- 不变量 5：attempt 递增必须可信且可对齐。
	- 规则：每次重试 `attempt + 1`，并且在 span/log/DB 三处一致。

adopted:

### 5) 常见“手测爆坑”根因与排坑顺序（从最常见到最致命）

draft:
- A. worker 一直 `claimed=0`
	- 原因：队列空 / 过滤条件不匹配 / claim 策略拿不到锁 / 被其它 worker 抢走 / reclaim 干扰。
	- 解法：做一个“单条注入事件”的 fixture：插入 1 条 pending；worker `batch_size=1`；跑 10 秒后退出并导出证据。
- B. trace 查不到（但 worker 明明在跑）
	- 原因：OTLP 协议/端口不匹配（grpc vs http/protobuf），或 exporter 没 flush。
	- 解法：优先用最稳的 gRPC 4317；并确保进程退出前 flush。
- C. shared keys 写错（例如 outbox_event_id 写成 entity_id）
	- 原因：字段名散落、多处 copy/paste。
	- 解法：只允许通过统一的 ObsContext/Helper 写入（例如 `set_outbox_event_id(...)`），禁止业务代码直接 set tag。
- D. 明明失败但 batch `result=ok`
	- 原因：batch 级 result 默认 ok，异常路径没回填；或 error 只在子 span，不上卷到父 span。
	- 解法：强制“result 汇总规则”：任何关键子 op 失败，batch result != ok。
- E. Jaeger 查询返回 `limit/total=0` 的假象
	- 原因：Jaeger Query API 元数据不一致（已知会误导）。
	- 解法：脚本用 `len(data)` 判定，不依赖 total/limit；lookback 设大一点。

adopted:

### 6) 推荐执行顺序（成功率优先）

draft:
- 1) 注入式 429（100% 触发，单条事件）
	- 目标：DB 状态进入 retry/backoff；logs/trace/metrics 都能按 `wordloom.outbox_event_id` 对齐定位。
- 2) 注入式 timeout（100% 触发，单条事件）
	- 目标：attempt 增长、`next_retry_at` 正常、span `error=true`、并且聚合 `result` 正确。
- 3) 注入式 4xx（不可恢复）
	- 目标：直接 failed + error_reason（不 retry）。
- 4) 压测式 429（真实性验证）
	- 目标：reason 聚合正确、metrics label 不爆炸、trace 仍可查。

adopted:

### 7) 平台化前的“实验外骨骼”（止血绷带，不是平台）

draft:
- 目标：把手测从“盯终端 + 凭记忆敲命令”变成“固定入口 + 自动导出证据”。
- 形态建议：一个统一入口脚本（shell 或 python），每个实验只接受三类参数：
	- `--rule`（注入规则）
	- `--outbox-id`（可选：绑定单条事件）
	- `--duration`（运行时长）
- 每次实验结束自动做三件事：
	- 导出最近 10 分钟 traces（复用现有 Jaeger 导出脚本）。
	- 输出一组“关键 metrics 查询提示”（让人能快速验收）。
	- 把关键日志按 shared keys grep 到一个小文件（避免人工翻屏）。

adopted: