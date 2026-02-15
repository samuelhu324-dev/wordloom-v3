1) “拆到对象存储”到底是什么？GC 又是什么？
1.1 拆到对象存储 = 把 blob 的“重东西”从 DB 拆出去

你现在的媒体体系本质上有两种东西：

内容本体（blob）：图片/视频的二进制数据，很大、很重、读写模式和 DB 很不一样

元数据 + 引用（refs/slots/events）：很小、要强一致、要可审计、要可查询

“拆到对象存储”的意思就是：

DB 里只保存：storage_key / blob_hash / mime / size / created_at ... 这类可查询、可审计的东西

真正的二进制文件放到：S3 / MinIO / 本地文件系统某个目录（也算“对象存储”的低配版）

refs 只指向 blob（通过 blob_hash 或 storage_key），而不是把文件塞进 DB

这会让 DB 回到它擅长的事情：事务 + 约束 + 查询 + 审计。

你现在“写磁盘 + 写 refs/blobs + 写事件”其实已经是在往这个方向走了：磁盘就是你当前的对象存储实现。

1.2 GC = Garbage Collection = 垃圾回收（媒体里通常是“孤儿 blob 清理”）

当你把 blob 放到对象存储后，会出现一个非常现实的问题：

用户上传了一张图（blob 已经写到对象存储）

但是后续写 refs 失败 / 用户取消 / replace 覆盖 / 软删 ref

结果：对象存储里留下了没人引用的 blob（孤儿对象）

GC 就是定期做：

找出“在对象存储里存在，但 DB refs 里没有任何指向它”的 blob

超过保留期（比如 7 天）就删掉

或者反过来：refs 被删了，触发一个“待回收队列”，异步清理对象存储

你之前看到我说 GC，是因为媒体系统如果走 blobs/refs 的工程化路线，GC 几乎是迟早要补的那一课：否则对象存储只涨不降。

2) 为什么 “Service 全包” 会逼你起真实数据库？而 Repo 能让替换变得有约束、可控？
2.1 关键区别：依赖方向（谁依赖谁）

Service 全包常见长这样：

use case 里直接拿 SQLAlchemy session

直接写 ORM model

直接 commit

直接拼 storage path，直接写磁盘

还在里面做业务决策（insert vs replace vs reject）

这种写法的后果是：
你的 use case 本身就“绑死”在 Postgres/SQLAlchemy/真实文件系统上。
所以你一跑测试，就不得不起：

真 DB（至少要有 transaction/unique constraint 行为）

真磁盘（至少要能落文件）

真依赖（甚至要有 Alembic schema）

2.2 Repo 的价值：把“可替换的外部世界”圈起来

引入 Repo（更严格点叫 Ports/Adapters）以后：

Application/UseCase 只依赖一个抽象接口：MediaRepositoryPort

真实的 SQLAlchemy 实现（Postgres）是一个 adapter：SqlAlchemyMediaRepository

你要换 DB/换存储/做回放/做 mock，只需要换 adapter

于是你获得了两个能力：

受约束的替换
你不能“随便换”，因为 Port 接口规定了契约：

需要哪些输入

产出什么输出

错误怎么表达

幂等怎么保证

测试不用起真实 DB（至少不用每次都起）
你可以：

用 SQLite 版本的 repo 实现（快速跑）

用 Fake repo（内存 dict）跑大多数决策逻辑

只有少数“约束/事务/并发”测试才上真 Postgres

你在媒体系统里强调的那套 WRITE(REQUEST/DECISION/DB/RESULT)，本质上就是把“决策”留在 application，把“持久化动作”下放到 repo。repo 只忠实执行，不做决策——这会极大提升可测性和可替换性。

3) 你给的 v3 media：怎么一眼看出 router / schemas / application(usecase) / ports / repo / model？

下面是你要的“看到某种代码形状，就知道它属于哪层”的判别法（你本地打开文件，按关键词搜就能定位）。

3.1 Router（HTTP 入口层）

典型证据：

APIRouter() / @router.post(...) / Depends(...)

参数里出现 Request、UploadFile、Form、Query、Path

返回 JSONResponse / ResponseModel

它应该做的：

解析 HTTP 输入（把杂乱请求“变干净”）

调用 use case

把 use case 的输出转成 HTTP 响应

它不应该做的：

insert/replace 的业务决策

SQL/事务

直接写磁盘路径策略（最多调用 storage port）

你现在 v2 的问题就是：入口散落（uploads.py / media.py 两条管线），导致审计/事件链条不完整。你现在把 cover 入口接到 v2 media pipeline，本质上就是把“入口统一”这步做对了。

3.2 Schemas（输入输出形状校验层）

你说你“没碰到 schema”，其实是因为你以前很多 endpoint 用的是：

直接 UploadFile + query param

或直接 dict / Any
所以 schema 存在感弱。

典型证据：

class Xxx(BaseModel): ...

字段类型、validator、Field(...)

用于 request body 或 response model

Schema 的作用不是业务逻辑，而是：

把输入“定型”：你期待的字段、类型、范围

把输出“定型”：前端依赖的稳定结构

把 400 提前（别让脏数据进 application）

你之前问过 “payload NOT VALID 硬约束会不会 500”：
正确做法是 schema 把它变成 400。
如果你绕过 schema（或者 schema 太弱），不合规数据落到 DB 约束（NOT NULL / CHECK）上，就很容易变成 500（取决于你有没有把 DB 异常转成业务异常）。

3.3 Application / UseCase（你现在叫 use_cases）

典型证据：

文件名像 upload_image.py

核心函数：execute(...) / handle(...)

里面出现：decision（insert/duplicate/replace/reject/noop）

它调用 ports：repo.save(...) / storage.put(...) / event.append(...)

它应该拥有：

业务决策（你那套 WRITE_DECISION 的核心）

幂等策略（同 request_id / 同 blob_hash 怎么处理）

调用多个 repo 的编排（事务边界通常在这里或 repo 层）

3.4 Ports（input/output）

你提到的 input.py / output.py，一般是：

Input port：use case 的调用接口（给 router 用）

“我提供什么方法给外部调用？”

Output port：use case 依赖的外部能力接口（repo、storage、event bus）

“我需要外部世界提供什么能力？”

典型证据：

Protocol / ABC / abstractmethod

只有方法签名，没有实现

名字像 MediaRepositoryPort、StoragePort、EventWriterPort

这就是“契约”的具体落地：系统从此有了清晰的可替换边界。

3.5 Repo implementation（基础设施适配器）

你给的 media_repository_impl.py 属于这一层。

典型证据：

import SQLAlchemy session / ORM models

add/commit/execute/select

不出现 insert vs replace 的业务判断（最多做 upsert 的技术实现）

Repo 的核心价值一句话：

把 application 的决定，落到现实世界里。

3.6 Model（ORM/表结构）

你给的 media_models.py 属于这一层。

典型证据：

__tablename__

Column(...) / relationship(...)

纯数据结构，不写业务决策

你之前问：“业务不复杂能不能没有 ORM model？”
能，但代价是：

SQL 字符串散落各处

约束语义不集中

迁移/重构成本更高

所以不是能不能，而是什么时候值得：

小脚本/一次性任务：可以不用 ORM

长期演进系统：最好有 model（哪怕很薄）

4) 回到你的三问：我给你一个“现在你处在哪一步”的定位

从你最新反馈看，你已经完成了这些关键里程碑（非常像“老系统合并管线”的标准打法）：

✅ cover 上传已经改走统一的 media v2 pipeline（refs/blobs + 事件）

✅ notes/bookshelves 加了 workspace_id 的 DB 兼容字段，避免 runtime crash

✅ 加了 helper（ref_id -> blob -> local URL）让前端可渐进迁移

✅ healthcheck 2-3 条写了（很好，说明你在做可验证链路）

这对应到你那张“验收标准图”里：

Router ✅（入口统一）

Service/Application ✅（decision 在 usecase/service）

Repo/Model ✅（开始成型）

DB ✅（约束字段补齐）

Events ✅（至少写入链路在统一收口；下一步是完善回放/查询）

你现在最值钱的下一步有两个方向（二选一先做都行）：

方向 A：把“workspace 推导”从临时策略，变成可解释的契约

也就是你那张 Step3：

短期：推不出就 400（你现在这样）

中期：回填 notes/bookshelves.workspace_id（数据修复）

长期：入口都显式携带 workspace_id 或稳定从 session/context 得到

它的意义是：

让审计/隔离/聚合这三件事从“碰运气”变成“系统保证”。

方向 B：把 marker 的图片也完全并入同一套 refs/blobs（你提到的 57 条补齐）

你已经有了：

上传返回 ref_id

helper 能把 ref_id 解析成可用 URL
那你下一步就可以做“一次性 backfill”：

把旧的 marker.image_url 解析出 marker_id/position

为每张图创建 media_refs（entity_type=CHECKPOINT_MARKER, entity_id=marker_id, position=…）

将 marker.image_url 逐步弃用（兼容期双写）

这个会让你的系统从“两条管线”彻底合并成“一条媒体真理管线”。

5) 你问的“domain 层怎么画出来”？以及 “service 是不是 application？”

你现在这套命名已经很接近标准分层了，我用一句非常可操作的定义给你：

Domain：不关心数据库、不关心 HTTP、不关心文件系统；只关心“业务对象是什么 + 规则是什么”。

media 的 domain 可以是：MediaType enum、SlotKey(entity_type/entity_id/role/position)、MediaId、Policy(cover replace, marker append/reorder/delete)

Application/Service/UseCase：用 domain 规则做决策，并编排 ports 完成一条业务路径。

所以你说的“service 是不是 application”：在你现在的语境里，基本等价（你把 use_cases 当 application service 很合理）