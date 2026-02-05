1) 这些 payload 需要精简吗？actor_kind 和 source 要不要？

先给结论：actor_kind 和 source 建议保留（而且未来更适合“升列”，不该永远塞 payload 里）。

为什么 actor_kind 必要

你现在已经明确会存在：

user 触发

system 触发（重算、后台任务）

unknown（历史缺失/backfill）

如果只有 actor_id，你会遇到两类麻烦：

actor_id 可能为 NULL/固定 UUID，你得靠猜

审计/Timeline 文案需要“系统自动/用户操作/未知来源”的语义

所以：actor_kind 是“语义层防止伪精确”的关键字段。它的成本很低、收益很大。

为什么 source 必要

source（api/worker/cron/migration）对你这种有 outbox、daemon、ES worker 的系统，是定位问题的核心维度：

“为什么这条事件没有 actor？”——哦，是 worker/cron

“为什么事件重复/乱序？”——哦，是 migration/backfill

“为什么某段时间刷爆？”——哦，是 api 某路由/某 worker 重试

所以：source 是“排障维度”，也该保留。

那哪些字段可能需要精简？（按你的截图 1/2 分两类事件看）
A) 访问类 / visit logs（截图 1：GET /api/v1/books/{id}）

这类事件高频、低审计价值，你未来大概率会做 TTL 或直接默认不展示。建议 payload 最小化到：

✅ 推荐保留（最小集合）

correlation_id（串一次访问链路/排障）

source（api）

actor_kind（user/system/unknown）

provenance（live/backfill/legacy_import）

schema_version

⚠️ 可选（看你是否真的用它做“访问洞察”）

http.method

http.route（但 route 里带具体 book_id 会导致高基数、又长；建议改成模板路由，如 /api/v1/books/{book_id} 或 route_name）

❌ 建议删/降级

view_source：这个通常是你自己定义的来源标签（api.book.get）。如果你已经有 http.route + method 或者未来有 event_type=book_opened，它就有点重复。
更好的做法：把它变成 event_type（如 book_opened），而不是 payload 字段。

访问类的核心原则：能定位链路即可，别把 HTTP 细节当宝贝长期存。

B) 结果类 / derived 类（截图 2：maturity/recalculate 触发的 maturity_recomputed）

这类事件属于“解释层”，对 Timeline 文案有用。这里 payload 可以比 visit logs 稍丰富，但仍然要“证据最小化”。

✅ 推荐保留（你现在这套其实挺合理）

trigger（block_created / adjust_ops_bonus …）：解释“为什么重算”

delta、previous_score、new_score：解释“发生了什么变化”

stage：解释“状态机变化”

initial（如果你用它区分首次计算/重算）

correlation_id / source / actor_kind / provenance

http.method/route：可选（对排障有用，但不一定要永远保留）

⚠️ 可选改造（我会推荐你做，能大幅降低噪声）

现在出现大量 delta:0 的 maturity_recomputed。
我建议你加一个开关策略：

delta != 0：保留并显示在 Timeline

delta == 0：仍可落库，但标成 visibility="silent" 或归入 debug（否则时间线会被“无变化重算”刷屏）

“payload 精简”的最实用规则（你不用纠结每个字段）

你给 Chronicle 的 payload 定 3 条硬规则就行：

永远不放大字段：不要放 block content / before-after 全量（除非司法级回放）

每类事件有白名单：event_type → allowed keys（超出直接丢弃或记录到 debug）

访问类默认可过期：visit logs 必须能 TTL/归档，不然迟早拖死库

actor_kind/source/provenance/schema_version/correlation_id 这几个属于“信封核心字段”，保留是对的；未来你 Phase C 成列时，优先把它们升列。