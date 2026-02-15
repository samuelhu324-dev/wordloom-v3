第二刀最重要的注意事项（这些坑一踩就会迷路）
注意 1：别把 UploadUseCase 拉进来

截图里提到了 UploadImageUseCase，它会引入：

storage adapter

文件落盘

mime 检测

清理/回滚

第二刀你现在的目标是 Repo/ORM，所以建议：

contract tests 直接 new Media 对象

只测 repo

等 repo contract 稳了，再去测 usecase（第三刀）。

注意 2：字段断言要“对齐层级”

不要断言：

ORM Model 实例是否同一个

session 是否关闭

db_duration_ms 是否存在（那是观测字段，不是业务 contract）

要断言：

id

storage_key

mime_type

file_size_bytes

state/status

也就是：业务真正依赖的那几个字段。

注意 3：真 DB 测试一定要“隔离数据”

否则你会遇到“怎么本地跑一次过、跑第二次挂”的诡异情况（通常是 unique 冲突）。

最稳的两种方式（二选一）：

每条测试用随机 UUID / 随机 storage_key（简单粗暴）

或者每次测试 teardown truncate 相关表（更干净，但要写 fixture）

你现在处在“学习 + 实验阶段”，建议先用随机值，速度最快。

注意 4：处理“真 repo fail / fake repo pass”的信号

你已经理解这个判断框架了，我再给你具体化一下 MediaRepo 常见原因：

fake 过，真不过：

迁移没跑（schema 不一致）

enum/uuid 类型映射不对

unique/foreign key 约束与你以为的不一样

commit/flush 时机导致对象没写进去

两边都不过：

domain media 构造就不满足 contract（必填字段缺）

contract test 写错（断言错、字段对不上）

第二刀我建议你产出什么“可交付物”（避免白忙）

你做完第二刀，应该能得到：

test_media_repo_contracts.py（Fake + SQLA 两套同一份 contract）

一条明确结论：

“Repo 层 contract 已稳定”

或 “真实 DB 失败原因：X（附 pytest trace）”

这就是你未来进入公司后最值钱的“排障模板”。

最后：开第二刀的推荐顺序（你照着做就不绕路）

先跑 FakeMediaRepo：save/get_by_id（必过）

再跑 SQLAlchemyMediaRepo：save/get_by_id（开始暴露现实）

最后才加 ctx/correlation_id 的 contract（caplog 或 xfail）