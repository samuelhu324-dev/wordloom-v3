# Log-S2B: Observability Triage（Metrics / Tracing / Structured Logs 的分工与联动）

Status: draft
links:
- docs/architecture/runbook/run-004-observability-tracing.md
- docs/architecture/runbook/labs/labs-007-observability-tracing-api-outbox-worker.md

## Background
在排障/审计/取证场景里，metrics、tracing、structured logs 都在讲“真相”，但颗粒度和用途完全不同。
把它们看作三种传感器：雷达（metrics）/ 录音笔（logs）/ 行车记录仪（tracing）。
本 log 的目标是给出可复用的“分工口径 + 操作链路”，避免在事故中盲目翻日志海。

## What/How to do

### 1) 统一口径：三件套各回答什么问题
draft:
- Metrics（指标）：回答“系统现在健康吗？哪里在冒烟？”（趋势、阈值、告警、容量、影响面）
- Tracing（链路）：回答“这一次请求/这一个批次慢在哪里、卡在哪里、跨了哪些组件？”（瓶颈定位、因果链）
- Structured Logs（结构化日志）：回答“当时发生了什么细节？参数/错误栈/决策分支是什么？”（证据细节、复盘、审计）
- 推荐工作流（生态链）：Metrics 发现异常 → Tracing 定位链路/步骤 → Logs 读细节与原因 → 回到 Metrics 验证修复效果
adopted:


### 2) 排障（debug / incident）：从“范围”到“原因”的协作方式
draft:
- Metrics（先发现 + 再缩小范围）：
	- 发现异常：lag 上升、retry_scheduled_total 暴增、terminal_failed_total 上升、outbox_oldest_age_seconds 变大
	- 定位范围：是 search worker 还是 chronicle worker？是 DB 慢还是 ES 慢？是某个 event_type 吞吐掉了？
	- 判断影响：影响面多大、持续多久、是否回落
- Tracing（显微镜：找到慢/卡在哪一步）：
	- 按 service 找慢 trace（例如 `wordloom-search-outbox-worker`）
	- 按低基数 tags 过滤（例如 `projection=search`、`result=retry`）
	- 看 span 树：卡在 claim、sink、DB lock wait 还是外部依赖（ES/HTTP）
- Logs（法医解剖：解释为什么）：
	- 读取 batch_size、retry/backoff、attempts、错误 payload、error_reason 等关键细节
	- 用结构化字段定位 actor/correlation_id/决策分支，避免全文搜索
adopted:


### 3) 审计（audit）：证据链与“主证据/辅证”分层
draft:
- Metrics：通常只做“统计补充”（次数、拒绝率、分组趋势），不适合作为单条审计证据链
- Tracing：提供动作链条骨架（API → UseCase → Repo → Outbox → Worker → ES/DB），但通常存在采样，不应成为唯一证据来源
- Structured Logs + Chronicle/Audit Log：审计主证据
	- 需要稳定字段、可查询、可追溯：actor_id/actor_kind、resource、action、occurred_at、correlation_id、provenance、source、result
	- Tracing/Logs 作为增强证据：解释过程与细节（错误栈/参数/分支）
adopted:


### 4) 取证（forensics）：在不完美数据下复原因果链
draft:
- 关键原则：可关联性优先（correlation_id、actor/source/provenance/schema_version 等是“燃料”）
- 推荐 SOP（理想链路）：
	- 从“受害事实”出发（例如某本书 score 异常、某条数据丢失、ES 索引缺块）
	- 查 Chronicle/Audit Events：按时间窗 + 资源 ID（book_id/block_id）或 correlation_id 定位
	- 用 correlation_id 查 Tracing：若命中，快速得到跨组件因果骨架（哪一步出错/超时）
	- 用同一个 correlation_id 查 Structured Logs：拿到错误栈、参数、重试策略、落盘结果
	- 回到 Metrics：验证同一时间窗系统层面是否也有异常（ES 抖动、DB 延迟、队列积压）
- 字段规约（让三件套能“对上号”）：
	- Shared Keys v1（低基数，必须在 Metrics labels + Tracing attributes + Logs 字段都出现；用于“缩小范围/聚合”）：
		- projection（例如 search_index_to_elastic / chronicle_events_to_entries）
		- op（upsert/delete/mixed）
		- batch_size
		- attempt
		- result（ok/failed/success/partial）
		- （可选）reason（失败原因：unknown_exception / es_bulk_5xx / timeout 等；只建议用于 metrics/logs 的分类，不要引入高基数）
	- Shared Keys v2（高基数，可用于“单条证据链/取证”，不进入 Metrics labels）：
		- correlation_id（用于 correlation_id → trace/log 的 pivot；API span 上应存在该 tag）
		- trace_id / span_id（Logs ↔ Tracing 的 pivot；tracing enabled 时日志自动注入）
		- entity_id / book_id / block_id / outbox_event_id（用于定位单条记录；仅放 tracing/logs）
		- actor_id + actor_kind / provenance / source / schema_version（审计字段；以 Chronicle/Audit 为主证据，tracing/logs 为辅证据）
	- 最小落地清单（DoD）：
		- Metrics：outbox_* 指标至少能按 projection/op/reason/result 聚合
		- Tracing：关键 span（outbox.claim_batch / projection.process_batch）至少有 projection/op/batch_size/attempt/result；API request span 至少有 correlation_id tag
		- Logs：关键点至少有结构化事件 outbox.claim_batch 与 projection.process_batch，并带同名字段；同时具备 trace_id/span_id（tracing enabled 时）
	- 基数规则：
		- Metrics labels 避免高基数（不要把 book_id/entity_id/correlation_id 塞进 label）
		- Tracing attributes 可携带高基数（但仍建议把“常用过滤字段”保持低基数）
		- Logs 结构化字段尽量全量（为取证/复盘保留细节），并保持字段名稳定
adopted: