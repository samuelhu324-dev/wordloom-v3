现状结论（回答截图 1）

get_current_user_id 并不是定义在 library 模块里，而是全局的安全配置里：在 security.py:73。
目前它是“开发模式依赖”：只返回一个 user_id（支持环境变量 DEV_USER_ID 覆盖），并没有从 JWT 解析任何 tenant_id/library_id（JWT 的 create/verify 在同文件里，但没接到请求链路上：security.py:21-72）。
所以现在的结构不是“tenant 结构”，而是“单用户/多库（multi-library per user）”的形态：library 更像 workspace/container，而不是 tenant（tenant 还没出现）。
多租户/归属锚点盘点（回答截图 2）

代码里没有 tenant：全仓库 Python 代码未找到 tenant_id / Tenant / tenants 表相关定义（这意味着你现在从 tenant 表开始会是一次较大的 schema/逻辑引入）。
当前归属链条是：
Library：靠 user_id 归属（表 libraries），见 library_models.py:33-46。
Bookshelf：强制 library_id（FK 到 libraries），见 bookshelf_models.py:34-55。
Book：强制 library_id（而且是冗余 FK，文件注释明确用于权限检查），见 book_models.py:50-80。
Repo 查询约束（你现在最需要注意的风险点）

多个 repo 的 get_by_id 是“裸按 id 取”，不带 user/library scope：
Library：get_by_id(library_id) 不按 user_id 过滤，library_repository_impl.py:106。
Book：get_by_id(book_id) 只过滤软删，不按 library_id 过滤，book_repository_impl.py:128。
Bookshelf：get_by_id(bookshelf_id) 也不带 library_id，bookshelf_repository_impl.py:109。
这不一定立刻是漏洞（可能 usecase/route 层做了校验），但对“多租户/授权骨架”来说，这是你必须尽早收口的点：隔离不能靠“大家都记得加 where”。
下一步怎么做（最小、最不返工的骨架路径）

先把 library 明确成 workspace（隔离边界先用 library_id），不要立刻上 tenant 表
原因：你当前 auth 只有 user_id，tenant 即便加表也缺少请求上下文去解析/选择；而你已经在 Bookshelf/Book 上有 library_id，用它做 scope 最自然。
引入统一 Actor（authn 的输出）
最小字段：user_id + library_id(可选) + roles(可先空) + request_id(可选)
在路由里逐步替换 user_id: Depends(get_current_user_id)：例如 library 路由已有大量依赖，library_router.py:338。
引入统一 Policy/Authorization 入口（authz 的入口）
先只做两条规则就够：
“访问某个 library/resource 必须在同一个 library scope 内”
“写操作需要 role”（role 先可硬编码成 owner=library.user_id）
把 scope 校验落到 usecase/repo 里（至少二选一）
推荐做法（更稳）：给 repo 增加“带 scope 的读取方法”，例如 get_by_id_for_user(user_id, library_id) / get_by_id_in_library(library_id, book_id)，然后让 usecase 只用这些方法。
备选做法（改动更小但更靠纪律）：usecase 先 get_by_id 再校验 resource.library_id == actor.library_id 或 library.user_id == actor.user_id。
加一条最小测试：跨 scope 访问应返回 403
你现在已经有 auth 相关测试痕迹（比如引用 get_current_user_id 的测试），可以沿用现有测试风格扩展。
如果你愿意我直接动手落地，我建议从“Library 读取/修改”这一条链路开始（最少文件改动、最容易验证），先把 GetLibraryUseCase/UpdateLibraryUseCase 改成接收 actor 并做 library.user_id == actor.user_id 校验，然后再扩展到 Book/Bookshelf（因为它们已经有 library_id 字段，天然适合做 scope）。你希望我先从 library 还是 book 这条链路开始改？

如果它承载用户可编辑的真实状态 → 先做授权/隔离/审计骨架（SoT）。

如果它只是为了查询/展示/加速 → 先做投影可重建 + scope 跟随（Projection）。