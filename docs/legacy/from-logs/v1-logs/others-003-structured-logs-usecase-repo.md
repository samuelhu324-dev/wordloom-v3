下一步应该做什么（按收益/成本排序）
第一步：把 usecase / repo 的“层内日志”补齐（先深后广）

你截图里现在主要是在 media_router.py 打了：

media.get.request_received / success / not_found / failed
并且带了 correlation_id, media_id, layer, outcome, duration_ms 这些字段。

下一步要做的是让链路变成：

handler：请求进来 + 最终结果（你已经做了）

usecase：决策点（成功/拒绝/异常） + duration

repo/adapter：副作用（DB 查询/存储调用） + duration + rowcount/错误分类

为什么要先做“usecase/repo”？

你要能区分：慢到底慢在 handler 逻辑、usecase 决策、还是 DB 查询

你要能区分：not_found 是“真的没数据”，还是“repo 层异常被吞/被映射”

具体你要加什么日志（最小集）：

usecase：

event: media.get.usecase.start（可选）

event: media.get.usecase.success

event: media.get.usecase.not_found

event: media.get.usecase.failed

fields: correlation_id, media_id, layer="usecase", outcome, duration_ms, error_type?

repo：

event: media.repo.get_by_id

fields: correlation_id, media_id, layer="repo", db_duration_ms, row_count(0/1), db_error_code?

小技巧：repo 不要打 SQL 文本；打“statement_name/operation_name”就行，安全又好聚合。

第二步：把异常链条“保根因”

你现在（从之前那份 GetMediaUseCase 看）有一个 except Exception as e: raise MediaOperationError(...) 的模式。外部错误语义没问题，但内部可观测性要补齐：

在捕获处打日志：error_type=type(e).__name__

用 raise ... from e 保留 cause（对开发排查很关键）

这样你 500 的时候不会只看到“Failed to get media”，而是能看到它到底是 OperationalError、TimeoutError、还是你代码 bug。