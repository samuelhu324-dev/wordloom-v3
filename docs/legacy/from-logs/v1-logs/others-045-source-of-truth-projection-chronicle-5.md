1) 怎么把 others-044 变成“可执行”的止血 + 疗伤方案（建议按阶段落地）
你现在的直觉是对的：先别纠结 Score breakdown（派生视图），先把系统做成“未来每条事件都能追责、能串起来、能解释”，否则 Timeline 永远像噪声。

Phase A（止血，1–2 天）：先把“事件信封”补齐到不再丢
目标：不改表结构也能先跑起来（把信封字段先塞进 payload 里）。

必须做到：

actor_id：用户触发的事件 默认从认证上下文自动填，调用方不传也不会空。
correlation_id：每个请求一个（HTTP header X-Request-Id 或服务端生成），写入 payload.correlation_id。
source：api|worker|cron|migration（能区分系统派生事件）。
actor_kind：user|system|unknown（别把 unknown 混成 system）。
这一步做好后，即使事件语义还不全，你也能把“同一次操作的一坨事件”用 payload.correlation_id 收束，且能区分系统派生。

Phase B（疗伤，2–5 天）：建立“事件目录（Event Catalog）”，把 UI 语义落到稳定 Facts
目标：Timeline 展示项不要直接等同于 events；Timeline 是投影。你要做的是：

列出 Timeline/Score breakdown 里的“卡片/文案”
给每个卡片标注：它依赖哪些底层事实（facts）
规定：facts 必须稳定、可审计；分数/权重/阶段判断放到投影里（可版本化）
举例（从你前端看到的东西“提纯”）：

Tags configured 不是事件；稳定事实是：tag_added / tag_removed
Block milestones 不是事件；稳定事实是：block_created / block_deleted / block_type_changed
Recent edits 不是事件；稳定事实是：block_updated / book_updated（或更细）
Maturity recomputed 这是系统事件（可保留），但它应该引用触发源（至少 trigger + correlation_id）
Phase C（产品化，后续）：把信封字段从 payload “提升为列 + 索引”
当你验证方案有效后，再考虑 DB migration：

correlation_id、actor_kind、source 变成列（可索引，查询/排障/分页更稳）
schema_version（每类事件 payload 的版本号）也建议列化或固定在 payload 顶层
Phase D（历史 backfill）：只补“可证明事实”，并标注 provenance
历史数据通常补不全 actor/request 链路：

允许 actor_kind="unknown"
provenance="backfill"、backfilled_at 必须写
不要编造 request/actor（审计系统最怕伪精确）
2) 一个“可长期维护”的 payload 分类（建议你现在就采用）
建议把 payload 分成两层概念：

事件信封（Envelope）：跨所有事件类型都尽量一致的字段（稳定骨架）
事件语义（Semantic payload）：按事件类型变化，但用固定的结构块（避免变垃圾桶）
下面是推荐的 payload 顶层结构（你可以先把它作为约定；未来再迁移成列）：

{
  "schema_version": 1,
  "correlation_id": "req-123", 
  "source": "api",
  "actor_kind": "user",
  "provenance": "live",

  "refs": {
    "book_id": "…",
    "block_id": "…",
    "tag_id": "…"
  },

  "intent": { "name": "rename_book" },
  "change": { "field": "title", "from": "Old", "to": "New" },

  "trigger": { "name": "block_created", "cause_event_id": "…" },

  "metrics": [
    { "metric_id": "maturity_score", "unit": "points", "previous": 45, "next": 50, "delta": 5 }
  ],

  "facts": [
    { "fact_id": "tag_added", "tag_id": "…" }
  ]
}

2.1 分类规则（核心原则）
Facts（事实）要稳定：代表真实发生的动作/变更（增删改、关联变动）
Derived（派生）不要固化为事实：分数、权重、卡片完成度、阶段判断——放投影里算，可用 projection_version
系统派生事件允许存在，但必须可解释：
source="worker" / actor_kind="system"
trigger.name 说明由什么触发（update_book/block_created）
最好能带 cause_event_id（如果你能拿到）
3) 从 Score breakdown “提纯底层语义”：可以，但要选对粒度
你问“能不能从前端 score breakdown 提纯出不会因为规则变化而删除的语义？”——可以，但要提纯成“facts”，而不是把 score breakdown 里的文案/权重抄进来。

从你看到的结构（title/tags/cover/blocks/todo/visits/edits…）提纯后，推荐的稳定 facts 清单大概是：

Book
book_created
book_renamed（change.field="title"）
book_updated（摘要/属性更新）
book_soft_deleted / book_restored
book_moved
Block
block_created
block_updated（内容、类型、状态）
block_deleted（如有）
Tag（关联）
tag_added_to_book
tag_removed_from_book
Todo
todo_promoted_from_block
todo_completed
Cover
cover_changed
cover_color_changed
Metrics/Snapshots（系统派生，可选）
book_maturity_recomputed（系统事件，记录 trigger + 前后分数）
content_snapshot_taken
这样无论 score breakdown 的规则怎么变（权重、阈值、卡片文案），你都不需要删历史事件；只要升级投影版本重算 Timeline/summary。

4) 给你一套“payload 模板库”（按类型长期可维护）
A) 纯变更类（rename / cover / stage）

{
  "schema_version": 1,
  "correlation_id": "…",
  "source": "api",
  "actor_kind": "user",
  "refs": { "book_id": "…" },
  "change": { "field": "title", "from": "…", "to": "…" }
}

B) 关联类（tag add/remove）
{
  "schema_version": 1,
  "correlation_id": "…",
  "source": "api",
  "actor_kind": "user",
  "refs": { "book_id": "…", "tag_id": "…" },
  "link": { "op": "add", "relation": "book_tag" }
}

C) 实体创建类（block_created）
{
  "schema_version": 1,
  "correlation_id": "…",
  "source": "api",
  "actor_kind": "user",
  "refs": { "book_id": "…", "block_id": "…" },
  "entity": { "type": "block", "op": "create" },
  "attrs": { "block_type": "paragraph" }
}

D) 指标/重算类（maturity_recomputed）——把“算法版本”写清楚
{
  "schema_version": 1,
  "correlation_id": "…",
  "source": "worker",
  "actor_kind": "system",
  "refs": { "book_id": "…" },
  "trigger": { "name": "block_created" },
  "algorithm": { "name": "maturity", "version": "v1" },
  "metrics": [
    { "metric_id": "maturity_score", "unit": "points", "previous": 45, "next": 50, "delta": 5 }
  ]
}

关键点：不要把 score breakdown 的每个细项权重都写进事件；最多写 algorithm.version，需要解释时靠投影/快照表重算。

5) 你贴的 .next-dev/...js：可以当“语义清单来源”，但别当 SoT
那份 JS 是 Next dev 产物（编译后的 bundle），适合作为“我需要哪些语义”的参考，但不适合作为长期维护的事实来源。更稳的是在 frontend/src/... 的源文件里做一个“Timeline/Score breakdown -> Facts 映射表”，并把它抄到 others-044 的 Event Catalog。

你接下来如果要我帮你把计划落到代码上，我需要你选一个切入点
在下面三个里选一个（越靠前越快见效）：

先补信封字段：让所有 ChronicleRecorderService.record_event() 自动注入 correlation_id/source/actor_kind/schema_version（写入 payload）
先补 2–3 个关键 facts：block_created、tag_added_to_book、book_updated/book_renamed（让 Timeline 能“像人话”）
先写 Event Catalog（markdown 表）：把你现在 Timeline/Score breakdown 的项逐条映射到 facts + 投影规则版本
你回复选哪个，我再给对应的最小改动方案与文件级 patch。
