先审核：这份 GetMedia 作为结构化日志目标“完整吗”？
✅ 好的部分（适合当切入口）

语义很干净：只做 get_by_id + not found 转业务错误。

get_media

已经有明确的领域异常：MediaNotFoundError / MediaOperationError，很适合做错误分类。

get_media

⚠️ 目前不完整/会让日志“没牙”

缺少请求上下文（request context）

你现在只有 media_id，没有：

correlation_id / request_id

actor_id / user_id

workspace_id / tenant_id

调用来源（endpoint、client、ip 不一定要全要，但至少要 correlation）

结果：日志只能说“查了一个 media”，但不能回答“谁查的、从哪查的、为何查的”。

缺少关键业务语义：权限与可见性

“Get media”在真实系统里通常不只是存在性：

软删（deleted_at）是否可见？

workspace/owner 是否匹配？

role/permission 是否允许？

如果这些逻辑在别处（比如 handler 或 repo）你也要在日志里能看出来，否则排障会很痛。

异常处理太“糊”

现在 except Exception as e: ... raise MediaOperationError("Failed...") 会把所有非 NotFound 的异常都包成一个错误。

get_media

这对外是 OK 的，但对内如果不打结构化日志，会导致：

你只能看到“Failed to get media”

看不到根因分类（DB timeout? connection? serialization? bug?）

所以：要么这里打日志保留 root cause，要么保留 exception chaining（raise ... from e）+ 在上层统一记录。

没有时延与边界指标

“Get”这类读路径最常见的生产问题就是慢（索引/锁/网络），没有 duration 你很难定位。

你应该从哪切入？我建议从“最小闭环的观测链路”切

别一上来就搞 domain event 或全局框架。你现在的目标是：让一次 GetMedia 的执行，在日志里变成一条可追踪、可统计、可排障的“故事”。

最优切入点：从 router/handler 开始，把 correlation_id 注入进 usecase

原因很现实：usecase 本身没有请求信息，它天然拿不到“谁、从哪来”。如果你从 usecase 直接加日志，最后会发现你缺一堆字段，又得回头改参数。

你可以这样分三层加探针（每层只打一类）：

Handler/Router：入口日志

event: media.get.request_received

fields: correlation_id, media_id, actor_id?, workspace_id?, route, method

UseCase：决策日志

event: media.get.not_found / media.get.success / media.get.failed

fields: correlation_id, media_id, result, duration_ms, error_type

Repository/Adapter：副作用日志

event: media.repo.get_by_id

fields: correlation_id, media_id, db_duration_ms, row_count(0/1), db_error_code?

这样你跑一次请求，就能看到：

“请求进来了”

“usecase 决策是什么”

“repo 实际查库发生了什么”

针对你这份 GetMedia：结构化日志应该长什么样才算“够用”？

我给你一个最低可用字段清单（能立刻把链路打通）：

必备字段（建议所有日志都带）

correlation_id（或 trace_id / request_id）

operation: "media.get"

media_id

layer: "handler" | "usecase" | "repo"

outcome: "success" | "not_found" | "validation_error" | "forbidden" | "error"

duration_ms（usecase 和 repo 至少要有）

错误场景必备字段

error_type（比如 "MediaNotFoundError", "MediaOperationError", "DBTimeout"）

error_message（内部日志可带；对外响应不要直接透出）

cause_type（如果你包了异常，至少在日志里记原始异常类型）

可选但很赚的字段（以后做指标/告警用）

workspace_id / tenant_id

actor_id（或 subject_id）

db_statement_name（不要打 SQL 字符串本体，打“语义名”）

cache_hit（如果你有缓存）

这份代码上，最小改动建议（不改变结构，只让它“可观测”）
1) 给 usecase 加一个 ctx（上下文对象）参数

不一定要大而全，最小就是：

correlation_id

actor_id（可空）

workspace_id（可空）

2) usecase 内记录三类日志：start / outcome / error

注意：start 日志可以省，因为 handler 已经记了入口。usecase 主要记 outcome + duration。

3) repo 里记 db duration + row_count

这样你能区分：

not_found 是真的没数据

还是 DB 抽风导致返回空/异常

你现在问“完整吗？”——我的判断标准

如果你按上面做完，你就达到了一个很实用的门槛：

看到一条 404：你能回答“谁查的、查什么、用了多久、DB 查到了没”

看到一条 500：你能回答“在哪一层炸的、根因类型是什么、是否 DB 相关、是否可重试”

以后要加权限/软删：你能在 usecase 日志里直接体现为 outcome=forbidden 或 outcome=not_found（避免泄露存在性）

我建议你第一刀就切这里

先从 handler 注入 correlation_id + 在 repo 打 db duration。
因为这两刀见效最快：你马上就能用日志把一次请求从头串到尾，之后再慢慢把 actor/workspace、权限语义加进来。