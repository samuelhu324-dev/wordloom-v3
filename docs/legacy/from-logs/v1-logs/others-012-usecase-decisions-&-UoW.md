实验 1（路线 A）：把“业务决策”写成一张表（不进 DB 的那种表）

目标：让你明确哪些逻辑该在 usecase、哪些不该在 repo/handler。

选模块：就用封面图（最合适），因为它天然包含“决策点”：

允许哪些 MIME？

最大尺寸？

已有 cover 时是否替换？是否删旧文件？

失败要不要回滚文件？

权限：谁能改 cover？

做法（最小动作）：

在 UploadBookCoverUseCase 或 UploadLibraryCoverUseCase 的 input/output 定义里，列出这些决策的结果枚举（success / rejected / not_found / forbidden / storage_failed …）。

写 6~10 条 usecase contract tests（先用 FakeRepo + FakeStorageAdapter）。

观察点：

你会突然发现：很多“应该写在 repo 的判断”其实是业务决策。

你也会发现：handler 只负责翻译 HTTP，不该带这些 if/else。

你不需要再打日志，测试结果本身就是观测：输入 → 输出 outcome。

实验 2（路线 B）：把 commit/rollback 的边界从 repo.save() 拿出来“看一眼”

目标：理解 Unit of Work / session 生命周期什么时候会成为硬需求。

选模块：还是封面图（因为它是典型的“跨资源一致性”问题）：

DB 更新 book.cover_media_id

文件系统/对象存储 写入文件

失败时要不要删文件？要不要回滚 DB？

做法（最小动作）：只做一个对照测试

case：存储写失败（FakeStorageAdapter 抛异常）

断言：

DB 的 cover_media_id 没变（回滚）

已写入的文件被 delete（补偿动作）
这会逼你回答：

commit/rollback 在哪里发生？repo 里？usecase 里？middleware 里？

你不需要真的实现完整 UoW，你只需要让自己能回答这句：

“当一个用例涉及多表 + 文件/外部系统时，事务边界必须外提。”

2) UoW 到底是什么？它是一个“新层”吗？放哪里？
UoW（Unit of Work）一句话

它是“事务边界管理器 + repo 集合的共享上下文”。
职责是：把一次用例涉及的多次 DB 操作，包进同一个 transaction，最后统一 commit/rollback。

它是不是一个新层？

更准确的说法是：它是应用层（Application Layer）里的一个组件/概念，不一定是“新目录层级”，但通常会单独抽成文件/类，因为它是通用能力。

常见摆放方式：

application/uow.py（推荐，清晰）

infra/uow_sqlalchemy.py（实现放 infra，接口放 application）

或者先临时写在某个 usecase 文件里也行，但最后大概率会抽出来

你可以把它理解成：
用例 = 剧本，UoW = 摄影棚的“开机/收工”流程（begin/commit/rollback）。
剧本不该自己拧螺丝，但它得决定“这一幕拍不拍成”。