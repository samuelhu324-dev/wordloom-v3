1) authn / authz：认证 vs 授权，边界在哪里？

authn（authentication，认证）：你是谁？
典型结果是：user_id（或 service identity）可信了。

authz（authorization，授权）：你能干什么？
典型决策是：这个 user_id 能不能对某个资源执行 read/write/delete/share/...

最重要的边界（建议你现在就固定）

API 层（入口）负责 authn：把请求变成“带身份的请求”
例如 FastAPI dependency 解 token → 得到 Actor(user_id, roles, tenant_id?)

Domain / Usecase 层负责 authz：对“领域资源”做权限判断
不要把权限散落在每个 endpoint 里，那会变成“到处 if user_id == ...”的灾难。

你可以先留的“骨架”

定义一个统一的 Actor（请求主体）

定义一个统一的 Permission/Policy 入口（哪怕先全放行）

每个 usecase 接收 actor，并在进入核心逻辑前做一次授权判断

这样以后你要加：共享、协作编辑、管理员、付费套餐，才不会爆炸。

2) 资源隔离：library / bookshelf / tenant 到底隔离什么？

这条是多租户的核心：谁的数据跟谁的数据绝对不能串。

你现在的模型很适合做隔离层级（按你提到的）：

tenant：公司/组织/空间（未来产品化最常见）

library：租户下的大容器（也可理解为 workspace）

bookshelf：再细一层的集合

book/block/...：具体内容

隔离有两种“硬度”

软隔离（逻辑隔离）：同一套表，用 tenant_id 列区分

优点：省钱、省事

风险：写错查询条件就越权

必做：所有表都带 tenant_id，所有查询都默认过滤它（最好 DB 层强制）

硬隔离（物理隔离）：不同 schema / 不同数据库

优点：更安全、更容易做“客户级备份/删除”

成本：运维更复杂

你现在不做多租户，也建议做的一件事

把“资源归属链”设计出来：任何资源都能回答：它属于哪个 library/bookshelf/tenant？

数据表上至少保留 owner_user_id 或 library_id 这种“归属锚点”

查询时始终从“归属锚点”出发，不要裸查资源 id

3) 审计日志：谁改了什么、什么时候（以及从哪儿来的）

审计日志不是 debug log。它是：事后追责 + 安全取证 + 合规。

你最少要能回答：

谁（actor）

什么时候（timestamp）

对哪个对象（resource type + id + scope，比如 library/bookshelf）

做了什么（action）

改了什么（可选：before/after 摘要）

从哪来的（request_id / ip / user-agent 可选）

最适合你这种 outbox/worker 架构的做法

API/Usecase 写业务数据时，同时写一条 audit_event（可以也走 outbox）

worker/后台任务同样写 audit（否则后台改数据就“无痕”了）

指标上你甚至可以做：audit_events_total{action=...}

“先留骨架”的最小实现

先只记录：actor_id + action + resource_id + time + request_id

不一定要存全量 before/after（那会很重），可以存字段列表或 hash

4) 数据脱敏与备份策略：数据如何“活下来”和“别泄露”

这条分两件事：泄露风险 与 灾难恢复。

数据脱敏（尤其日志、导出、测试数据）

你做 Wordloom 这种知识内容系统，最容易泄漏的是：

原文/译文内容（用户隐私）

搜索索引（ES 常被当成“可随便查”的系统，最危险）

错误日志里把 payload 打出来

最常见的坑：为了排查问题把内容全打进日志/指标，然后日志系统成了“第二数据库”。

建议你定个简单规则：

日志里默认不打 content，只打 content_length/hash

出错时只采样少量、且脱敏（mask email/phone/token）

测试环境用 synthetic 数据，不用真实导出的

备份策略（能恢复才叫系统）

最朴素但有效的三件套：

Postgres 定期备份（快照 + WAL/增量，目标是能恢复到某个时间点）

ES 可重建（索引是 projection：能从 source-of-truth 重放出来）

对象存储（S3/本地）生命周期（媒体/附件要备份 + 校验 + 过期策略）

你现在的架构其实天然有利点：
只要你认定 Postgres 是真相源，ES 和其他投影都应该能重建。
那备份优先级就清晰了：PG > Object Storage > ES（ES 可以不备或只备配置/模板）。

你现在“还没做多租户”，怎么把权限模型留骨架？

一个很实用的落地顺序（不会把你拖进大工程）：

引入 Actor（usecase 统一入口参数）

每张核心表都能追溯归属（至少 library_id / owner_user_id）

写一个 Policy 接口（先全允许，但入口固定）

加 audit 表（先记 action + resource + actor + time）

日志脱敏规则（尤其 content 不进日志）

明确 source-of-truth（PG 是真相，ES 可重建）→ 备份策略就顺了

这一块学完，你会发现它跟你前面学的 daemon/lease 是同一类思维：
系统不是“能跑就行”，而是“能负责、能追、能恢复、能扩展”。