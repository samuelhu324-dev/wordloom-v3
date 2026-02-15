你路线 B（worker/daemon 抗坏+自愈）收尾得很漂亮；路线 C 这块你别上来就“搞多租户/审计/安全大工程”，否则又会进入无底洞。正确开头是：先把“Actor + Request Context + Policy”做成一条最小闭环链路，让系统从“靠手写 owner check”升级为“统一骨架”，但成本可控。

下面给你一个可以直接开工的起手式（按你现在 Wordloom 的结构最贴）。

路线 C 的正确开头：先做“统一 Actor 骨架（MVP）”

目标一句话：每个请求都能得到一个标准化的 Actor 对象；每个需要权限的动作都走 Policy；每个重要动作都能落一条审计日志（Chronicle）。

你已经有 owner check（Library/Bookshelf/Book），那说明资源边界（Resource）是清楚的。接下来不要扩展到“真正多租户”，只做“把权限和审计从 if-else 散落收敛到骨架”。

Step 1 — Actor 模型（最小，不引入 roles 也能跑）
1.1 定义 Actor（请求级）

建议最小字段：

user_id（可空：system/anonymous）

actor_kind：user | system | anonymous

request_id/correlation_id（用于追溯）

library_id（可选：如果你已经能从 token 或 path 推导）

roles（先别做复杂，留空或只做 owner）

关键：Actor 是“请求上下文”，不是 DB 表。
你先别急着建 Actor 表（那是产品化以后才需要的）。

1.2 Actor 从哪里来？

API 请求：从 auth token 解析出 user_id（你现在应该已有）

worker/daemon：用 SYSTEM_ACTOR_ID + actor_kind=system

未登录：actor_kind=anonymous

你在 Chronicle Phase C 已经做 envelope/correlation/provenance 了，这里刚好能复用：Actor 就是“安全骨架”和“审计骨架”的共同输入。

Step 2 — Request Context（把 Actor 贯穿全链路）

你需要一个“单一入口”把 Actor 放进上下文，避免未来再出现 actor_id 传丢。

做法（概念级）：

在 API 层 middleware：构建 RequestContext(actor, correlation_id, source)

在 usecase/service 层：只拿 context，不允许函数参数到处传 user_id

这一步的验收标准很简单：

任何写操作 usecase 都能拿到 Actor

Chronicle 记录不再依赖“调用方记得传 actor_id”

Step 3 — Policy/Authorization（从一个最小 Policy 开始）

你现在的 owner check 是散的。下一步不是“写一套 RBAC”，而是：

3.1 先做 1 个 Policy：BookPolicy

提供 2 个方法就够：

can_view(actor, book)

can_edit(actor, book)

内部先继续用你现有的 owner check 逻辑，但把它搬进 Policy，以后所有地方只调用 Policy。

3.2 验收标准（DoD）

所有 book 的写操作入口（rename/update/add block/tag）都调用 BookPolicy.can_edit

API/router 不再出现散落的 if-else owner check（或只剩极少）

这一步一旦完成，你就从“手搓权限”升级为“规则集中表达”。这就是骨架。

Step 4 — 审计日志（先接 Chronicle，不要另起炉灶）

你截图 2 里写“审计日志（谁在什么时候对什么资源做了什么）”，你已经有 Chronicle，所以别再造一个表。

起手最小审计事件（只做 3 个最常见的）：

book_renamed

tag_added

block_created

每条写入 Chronicle 的 payload 只放审计必需字段：

actor（actor_id/actor_kind）

resource（book_id/block_id）

action（event_type）

correlation_id/source/provenance

before/after（只放摘要，不放大文本）

DoD

任意一次 book_renamed，Chronicle 能查到“谁改的、改了什么、在哪个请求里发生”

worker/daemon 触发的动作能标记 actor_kind=system

Step 5 — 备份/脱敏（先写“策略文档 + 最小导出”，别做产品）

你截图 2 的“数据备份/脱敏策略”是未来产品化必经之路，但开头别做自动化系统。

起手做两件事即可：

写一页策略：哪些数据敏感、日志/Chronicle 不允许落什么（比如 block content）

最小导出命令/脚本：能导出某个 library 的 metadata（不含内容）

这就够你把路线 C 从“愿望清单”变成“可开工工程”。