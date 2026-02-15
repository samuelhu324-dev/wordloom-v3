-1-

入口（router）：media.file.request_received（证明请求命中了这个 handler）

数据（repo）：media.file.db_loaded（证明确实查到了 media 元数据，且记录 db 耗时）

存储（storage）：media.file.storage_resolved（证明拿到了文件路径/对象存储 key，且记录 storage 耗时）

出口（router）：media.file.response_prepared（证明准备返回文件，带 size/content_type）

出口（router, 发送完成）：media.file.response_sent（证明响应发送完成；统计耗时以 total_duration_ms 为准）

统一出口（middleware）：http.response（统一记录 status_code / duration_ms）

全局入口（middleware）：http.request_received（证明请求进入应用；固定 correlation_id）

全局 422（exception_handler）：schema.validation_failed（证明 schema 校验失败；通常不会进入 handler/usecase）

统计口径（强烈建议固定下来）：

- 下载链路耗时：以 media.file.response_sent.total_duration_ms 为准（prepared 只用于诊断，不做 SLA 口径）
- 错误分类：优先看 media.file.not_found / media.file.file_missing，再结合 http.response 的 status_code

4) 把“事件 → 文件/模块”的映射固定成一张表（你以后排障会快很多）

你现在已经有稳定的 event name，这意味着你可以制定一套规则：

media.file.* → modules/media/routers/media_router.py

media.repo.* → infra/storage/media_repository_impl.py

http.response → middlewares/payload_metrics.py（或类似）

ui.image.* → frontend/.../imageMetrics.ts

以后你只要看到一个 event，就知道“应该去哪一层改”。

如果你再进一步：给每条日志加一个字段 src（模块名）或 code_location（手写常量，不要自动堆栈），你连 grep 都更省事。

5) 给你一个“别再补日志”的护身符：事件字典

http.request_received

http.response

schema.validation_failed

usecase.outcome

repo.query（可选，仅当你真需要 db_duration_ms）

你以后要加新事件，先问一句：它能回答哪个新问题？如果不能，就不加。

6) 截图式“3条简单验证”快速命令（PowerShell）

把你这次动作的 CID 填进去（上传封面/设置封面时前端传的 X-Request-Id 或 img 的 ?cid）：

`$cid = "<CID>"; Get-Content backend\server.log | ForEach-Object { try { $_ | ConvertFrom-Json } catch { $null } } | Where-Object { $_ -and ($_.correlation_id -eq $cid -or $_.cid -eq $cid) } | Select-Object ts,event,operation,outcome,status_code,method,path | Format-Table -Auto`

你应该能看到：

- 成功：`http.request_received` + `usecase.outcome outcome=success` + `http.response status_code=2xx`
- 典型 4xx：`http.request_received` + `usecase.outcome outcome=not_found|forbidden|conflict` + `http.response status_code=404|403|409`
- 典型 422：`http.request_received` + `schema.validation_failed` + `http.response status_code=422`


