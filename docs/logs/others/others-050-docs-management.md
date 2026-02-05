2) 你“记不得做到哪了”：给你一套产品文档与推进的管理办法（不靠意志力）

Status: Adopted
Related milestone: Docs management system

Key outcomes:
- 建立唯一指挥中心：docs/ROADMAP.md
- 建立模块状态档案：docs/<module>/STATUS.md（先从 Chronicle 开始）
- 重要决策沉淀为 ADR：docs/adr/ADR-0xx-*.md

Next actions:
- 为 logs/others 引入统一状态头（模板：docs/logs/others/_template.md）
- 把 Chronicle 相关的核心决策提炼为 1 页 ADR（envelope/去重/visit TTL）

Links:
- ROADMAP: [docs/ROADMAP.md](../../ROADMAP.md)
- Chronicle STATUS: [docs/chronicle/STATUS.md](../../chronicle/STATUS.md)
- ADR: [docs/adr/](../../adr/)

你现在的症状非常典型：计划散落在 logs/others 里，缺少一个单点 SoT（source of truth）来承载“当前状态”。解决方案不是写更多文档，而是建立一个很小但强硬的结构：

2.1 建一个唯一的“指挥中心”文件：docs/ROADMAP.md

它只做三件事：

当前版本目标（比如 Chronicle v2/v3…）

正在做什么（Now）

下一步做什么（Next）

模板你可以直接用：

Current focus（1 行）：Chronicle Phase C: envelope columns + TTL for visit logs

Done（只列里程碑，不要细节）

Now（最多 5 条）

Next（最多 10 条）

Blocked / Risks（最多 5 条）

所有 “others-0xx” 的实验记录都只能引用它，不允许反过来让计划藏在实验记录里。

2.2 建一个“版本里程碑”文件：docs/chronicle/STATUS.md

这里把你说的 v1-v4 写清楚，并且每版只允许 3 类信息：

scope（这一版解决什么）

exit criteria（什么叫做完）

links（指向相关的 ADR / logs / PR）

你现在最缺的是 exit criteria，所以你才会“做到一半忘了”。

2.3 建一个“决策仓库”：ADR

你已经在写很多 “source-of-truth-projection …” 类文档了，但它们看起来更像日志而不是决策。把它们收敛成：

docs/adr/ADR-0xx-chronicle-envelope.md（为什么要 actor_kind/source/correlation 升列）

docs/adr/ADR-0xx-chronicle-dedupe-window.md（为什么 DB 级去重，而不是内存）

docs/adr/ADR-0xx-chronicle-visit-ttl.md（访问日志为什么 TTL）

ADR 的好处是：你以后忘了，不需要读 20 篇实验日志，只读一页“当时为什么这么决定”。

2.4 给 logs/others 加“归档机制”：每篇都必须有状态头

你不需要删旧文件，只要每篇顶部加 6 行：

Status: Draft / Adopted / Superseded / Archived

Related milestone: Chronicle v2

Key outcomes: 3 bullets

Next actions: 3 bullets

Links: PR/ADR

然后每周一次，把 Draft 要么升级成 ADR，要么标 Archived。

2.5 每周一次“10 分钟收口仪式”（真的很关键）

固定动作：

从 ROADMAP 里勾掉 Done

Now/Next 重新排 1 次

把本周新增的 logs 归档到对应 milestone（只做链接，不搬运内容）

这相当于你给系统做 GC（垃圾回收）。不做的话，计划会像内存泄漏一样把你脑子撑爆。

你现在就可以立刻执行的“最小改动”

新建 docs/ROADMAP.md（指挥中心）

新建 docs/chronicle/STATUS.md（v1-v4 + exit criteria）

把你截图 3 那堆 others-0xx 里最关键的 3 篇，提炼成 3 个 ADR（每篇一页）

以后所有新实验日志都必须链接回 ROADMAP 的某条 Now/Next

这样你下次再忘记“做到哪”，只要打开 ROADMAP，你就能瞬间回到主线，不用在 others 文件夹里考古。