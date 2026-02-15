1) SoT 是什么？

SoT = Source of Truth，中文通常叫：

真相源 / 主数据 / 记录系统（System of Record）

意思是：“这份数据到底以谁为准？”

一个数据如果是 SoT，说明它满足（或你希望它最终满足）：

强一致/强约束：不能随便“差不多”

写入有规则：要校验权限、隔离、约束、事务

审计有意义：谁改了什么、何时改的，有价值

在 Wordloom 里最典型的 SoT 就是你已经在做的那条链：

Library / Bookshelf / Book / Block（以及任何会被用户直接编辑、会改变业务状态的东西）

2) “每个模块五行”是要改代码吗？还是写到哪里？

优先答案：这是“边界清单/设计账本”，先写文档，不是先改代码。

你图里那“五行”本质是一个模块边界卡片（Boundary Card）：用极少的信息让你回答——

这个模块到底是 SoT 还是投影？
它的隔离键（scope key）是什么？
它有哪些写路径？
依赖哪些投影？
需要什么一致性等级？

建议放哪儿（很实用的落地方式）

给你一个最顺手的结构（不需要大重构）：

docs/architecture/module-boundaries.md（总表，一页看全局）

docs/architecture/modules/<module>.md（每个模块一页，五行 + 备注）

再写一份 ADR（可选但很值）：

docs/adr/ADR-0xx-sot-vs-projection.md

为什么不写在 domain 里？
因为这是“跨模块治理规则”，它属于架构层/系统级文档；domain 里写会把纯业务模型污染成“组织章程”。

什么时候才需要改代码？

当你写完这些卡片后，你会自然发现两类“必须改代码”的点：

SoT 模块：要补齐 owner/scope/权限/审计/事务边界（你现在在 usecase/repo 做的就是这个）

投影模块：要保证能 rebuild、能过滤 scope、能容忍 eventual consistency

也就是说：五行先让你看清“应该在哪改、改到什么程度”，不是让你立刻全库动刀。

3) 为什么先只分 Source of Truth 和 Projection？听起来太粗了

粗，正是它的美。

你现在的阶段最需要的是一个稳定的二分法，把 80% 的架构决策瞬间变简单：

A. SoT（真相源）

你必须关心：事务、约束、权限、审计、强一致

出问题后：不能“重建一下就好”，因为它就是现实本身

B. Projection（投影/派生/读模型）

你必须关心：可重建、可延迟一致、失败可恢复、吞吐、索引策略

出问题后：通常可以“重放/重建/补偿”，因为它不是最终真相

很多看似“第三类”的东西，最终都会被你归到这两类里：

Cache：本质也是投影（可丢可重建）

Search index / Stats / Dashboard / Chronicle 聚合：投影

Outbox / event log：它是 SoT 还是投影？取决于你怎么定义

如果你把 outbox 当“可靠的系统账本”（例如事件溯源那种），它接近 SoT

如果它只是“投影队列/中间态”，它更像投影（可重放可修复）

所以先二分，是为了让你先把“该严肃的地方严肃起来”，别把投影也当亲儿子供着（那会很贵）。

4) “我是不是要先把授权/隔离/审计全模块统一梳理完，才能开始 SoT vs 投影分离？”

不需要，而且如果你这么干，你会陷入“全图景完美主义 -> 永不动工”。

更聪明的顺序是：

先写边界清单（五行卡片）：全模块都写，但只写到“能分类 + 能落 scope key”

先把 SoT 主链路做对：Library → Bookshelf → Book → Block

因为它们是“写入路径的核心”，安全/隔离在这里最值钱

投影模块只做最低限度的正确：

必须带 scope key（例如 library_id）

查询必须按 scope 过滤

允许 eventual consistency（延迟更新没关系）

最后再扩展到 media/search/stats 等：它们会因为你前面 SoT 的边界清晰而变简单

一句话：先把“真相源”治理好，投影会自动变乖。

5) 给你一个“模块五行卡片”的模板（你可以直接抄）

对每个模块填这个（真的只要 5 行，备注另写）：

SoT?（Y/N；若 N 就是 Projection）

Scope key（library_id / user_id / book_id -> library_id）

Write paths（create/update/delete/move/restore…）

Depends on projections（search/stats/chronicle… 依赖谁）

Consistency（strong / eventual；允许延迟多久；失败如何恢复）

举例（你现在已经很接近这个状态了）

Book 模块

SoT: Y

Scope key: library_id（或 book.library_id）

Write: create/update/delete/move/restore

Depends: search projection（写后异步更新索引）

Consistency: SoT strong；search eventual（比如 1~10s 可接受）

Search 模块

SoT: N（Projection）

Scope key: library_id（必须带）

Write: rebuild/index/upsert/delete（由事件驱动）

Depends: book/block SoT

Consistency: eventual；可重建；失败重试 + backoff

你现在问的这些，已经从“会跑”进入“会负责”的阶段了：系统开始像一个产品，而不是一堆能动的代码。

下一步你会明显爽很多：当你再看一个模块（比如 media / chronicle / stats），你不会再问“我要不要重构”，你会问：

它是 SoT 还是投影？
它的 scope key 是什么？
它允许多慢？能不能重建？

这种问题会把工程从“宗教战争”变成“物理规律”。

你现在执行 SoT vs Projection 分离的正确姿势（按你这份计划书落地）
核心原则很简单：先写“边界清单（五行卡片）”，再改“事件/投影管道”，最后才是“把读请求迁移到投影”。不要一上来重构一堆目录。

0) 先定范围：先做一条“最小闭环”即可
建议你第一轮只选 1 个投影目标，例如：

Dashboard/Stats 聚合（最常见、最容易 eventual）
或 Search Index（也很典型）
不要同时做多个投影，否则会被一致性/回放/失败恢复拖爆。

1) 先写文档：模块五行卡片（这是执行开关）
按你文档里的建议，先落在仓库里（先文档，不改代码）：

docs/architecture/module-boundaries.md（总表）
docs/architecture/modules/<module>.md（每模块 5 行卡片）
可选：docs/adr/ADR-0xx-sot-vs-projection.md（为什么这么分）
怎么做（操作步骤）

列出所有模块（用搜索辅助）
在 backend 下跑：
对每个模块填 5 行（先“能分类+能落 scope key”即可）。
你主链路已经很清楚：Library/Bookshelf/Book/Block = SoT（强一致）
投影候选通常是：search、stats、chronicle、dashboard、cache 类。
验收标准

每个模块都有：SoT?/Scope key/Write paths/Depends/Consistency
SoT 的 scope key 统一（你现在基本是 library_id）
2) 画清“写路径”：SoT 写入要产出事件（outbox）
SoT 与投影分离的工程落点是：
所有 SoT 写操作（create/update/delete/move/restore…）在同一事务里写 outbox 事件，投影消费者异步处理。

你要做的事（操作步骤）

选定事件边界：以 SoT 为准（Book/Block 的变化最有价值）
定义最小事件 schema（先别追求完美）：
event_id, occurred_at, type, scope_library_id, aggregate_id, payload_json, version
在 SoT 的 usecase 成功写入后，同事务插入 outbox（事务边界要一致）
验收标准

SoT 写入成功 ⇒ outbox 一定有事件
SoT rollback ⇒ outbox 也不能出现事件（同事务）
你在 others-012-usecase-decisions-&-UoW.md 里提到的 UoW/事务边界，就是为这一步服务的：只要出现“DB + 外部系统/多表一致性”，事务边界必须外提到 usecase 或 middleware/UoW。

3) 建投影：Projection 表/索引必须“可重建 + 带 scope key”
投影要满足两件事：

可重建（rebuild）
查询必带 scope key（library_id）
怎么做（操作步骤）

为投影建独立存储（表或索引），字段冗余是允许的
写 consumer：订阅 outbox 事件 → upsert 投影
写 rebuild 命令：从 SoT 全量扫描重建投影（或从事件重放）
验收标准

清空投影后能一键 rebuild 恢复
投影查询不会跨 library 泄露（强制 library_id 过滤）
4) 迁移读路径：先加“双读/灰度”，再切换
不要一次性把所有查询换成投影。

推荐顺序：

先保留原 SoT 查询作为兜底
新增投影查询接口（feature flag）
对比结果（shadow read），稳定后切换
验收标准

线上出现投影延迟/失败时，不影响 SoT 写入
投影故障可通过 rebuild 恢复
5) “能不能直接交给 agent？”
可以交给 agent 的部分（机械工作）：

扫描模块、生成五行卡片模板、在仓库里创建 docs 骨架
按既定 schema 生成 outbox 表/ORM/迁移脚本骨架
生成 projection consumer/rebuild 命令的脚手架
全局检索并标注 SoT 写路径（usecase 列表）
不建议完全交给 agent 的部分（需要你拍板的系统决策）：

哪些模块是 SoT vs Projection（边界）
scope key 选型（library_id vs tenant_id）
一致性目标（哪些必须 strong，哪些允许 eventual，延迟 SLA）
事件 schema 的稳定性与版本策略
你现在下一步最该做什么（最小可执行清单）
先建 docs/architecture/module-boundaries.md（总表），把模块先二分
选 1 个投影目标（stats 或 search），明确它的 scope key = library_id
给 Book/Block 的写用例加 outbox（同事务）
写一个最小 consumer + rebuild 命令，让投影可重建
最后迁移 1 条读 API 到投影（加 feature flag）
如果你告诉我：你想先做 Stats 投影 还是 Search 投影，我可以把“具体到文件/目录/类名”的执行步骤拆成一份逐条 checklist（含你在 VS Code 里该搜什么、先改哪几个 usecase）。