我建议你用一种很稳的结构：

Status: Adopted
Related milestone: Docs management system

Key outcomes:
- 约束 ROADMAP 与 STATUS 的链接方向：ROADMAP 指向 STATUS；STATUS 只反向引用一条 Current work
- 约束 logs/others 的归档：必须有状态头；必须被 STATUS 引用，否则按“孤儿日志”每周清理
- 约束决策沉淀：重要决定提炼为 ADR（1 页，回答“为什么”）

Next actions:
- 以 Chronicle 为样板：完善 docs/chronicle/STATUS.md 并让 ROADMAP 的 Now/Next 全部指向它的锚点
- 新增/沿用 logs 模板：docs/logs/others/_template.md

Links:
- ROADMAP: [docs/ROADMAP.md](../../ROADMAP.md)
- Chronicle STATUS: [docs/chronicle/STATUS.md](../../chronicle/STATUS.md)
- ADR: [docs/adr/](../../adr/)
- logs template: [docs/logs/others/_template.md](./_template.md)

ROADMAP.md = 指挥中心（现在/下一步/风险）：只放“你接下来 1–2 周要做什么”，永远短。

各模块 STATUS.md = 模块档案（范围/现状/出口条件/历史链接）：放“这个模块整体怎么演进、已经做了什么、还缺什么”，可以长。

然后它们之间用 链接 联动，而不是自动同步。

你问的具体规则：Now/Next 怎么和 Status 联动？
1) Now / Next 里的每一条任务都应当“指向”某个模块的 Status

做法很简单：每条 Now/Next 任务都带一个模块标签 + 链接：

[Chronicle] Phase C: promote envelope columns (source/actor_kind/correlation_id) → 链接到 docs/chronicle/STATUS.md#phase-c

[Search] Fix ES outbox retry + DLQ → 链接到 docs/search/STATUS.md#dlq

这样你从 ROADMAP 一点进去，就能看到模块上下文与历史。

2) Status 里反过来引用 ROADMAP，但只引用“当前相关的一条”

在 Status 里加一个小块：

Current work (from ROADMAP): ...（一条链接即可）

避免把 ROADMAP 整段复制进 STATUS（那会发散）。

“完成后细节只要在 Done，其他保留在 Status 当历史档案？”——基本对，但要多加一条“决策沉淀”规则
Done 里放什么？

只放里程碑，不放过程。例如：

✅ DB-level dedupe for block_updated (chronicle_event_dedupe_state + upsert gate)

✅ Timeline ordering stabilized (occurred_at + id)

✅ actor_id propagation fix in book_router

Done 的作用是：让你 10 秒内知道“最近交付了什么”。

Status 里放什么？

Status 里保留：

scope（模块边界）

phases（v1-v4/Phase A-D）

exit criteria（每阶段完成标准）

“历史链接”（指向 logs/others、PR、测试、迁移脚本）

它就是“历史档案 + 现状说明书”。

那些“细节日志（others-0xx）”放哪？

照旧放 logs/others，但必须满足两条：

顶部有状态头（Draft/Adopted/Archived…）

在 Status 的对应阶段下被引用（否则就算“孤儿日志”，每周清理）

再加一条最关键的：重要决定要升 ADR

凡是你未来可能问自己“当初为什么这样做”的内容（比如 dedupe 的 DB 方案、TTL 策略、actor_kind 语义），要从日志提炼成 ADR。
ADR 是“为什么”；Status 是“是什么/做到哪”；logs 是“过程证据”。

一个很顺手的“工作流”

你开始干活：在 ROADMAP 的 Now 写一条（带链接到 Status）

干的过程中：写一篇 others-0xx 记录实验/排障

做完：

ROADMAP：从 Now 移到 Done（写一行里程碑）

STATUS：在对应 Phase 下打 ✅，加上链接（PR/迁移/测试/others）

若涉及关键决策：补一篇 ADR（或把 others 提炼成 ADR）

这样你永远不会“忘了做到哪”，因为：

看 ROADMAP：知道下一步行动

看 STATUS：知道模块全貌与历史

看 ADR：知道为什么这样设计

看 logs：知道当时怎么试出来的

这套结构有点像你系统里的 SoT 分层：ROADMAP 是“控制面”，STATUS 是“数据面”，logs 是“原始事件流”，ADR 是“不可变决策事件”。你会非常适应这种味道。