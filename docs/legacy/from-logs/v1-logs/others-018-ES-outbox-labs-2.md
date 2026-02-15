练习 A｜单事件追踪（最重要）

随便选一个 block_id

手动做一次更新

自己查三处：

blocks 表（业务状态）

outbox 表（是否有事件，processed_at 何时被填）

ES 文档（是否同步，version 对不对）

能不用看代码，只靠 SQL + curl 讲清楚这条链路，你就“内化”了。

练习 B｜故意制造失败

停掉 ES

再更新 block

看 outbox 堆积

再启动 ES / worker

看它是否自动追上

这是“最终一致”的肌肉记忆。

练习 C｜读日志，不读代码

看 worker 的 retry / backoff 日志

看 processed / error 的变化

学会“用日志理解系统状态”

如果你能做到这三点，记忆已经不是问题了。