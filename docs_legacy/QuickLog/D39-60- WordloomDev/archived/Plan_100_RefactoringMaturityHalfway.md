先按 Plan100 的结构来回答你目前的完成度。

一、Plan98 / Plan100 已完成的工作

独立成熟度模块落地（后端）

在 maturity 下已经有：domain（规则引擎 + 阶段策略）、application（Calculate / Reconcile 用例）、router 和 schemas。
新表 maturity_snapshots 已在 WSL2 的 Postgres 中创建并修订，字段包含：book_id, stage, score, components, tasks, manual_override, manual_reason, signals, created_at，并有 book_id + created_at 复合索引。
与 Book 的耦合度明显下降

评分与结构任务的细则从 book 模块迁出，集中在 maturity 的 rule engine 内；
Book 聚合主要保留阶段 / legacy 标记以及简单的 API，成熟度“怎么算”由 maturity 模块负责。
前端概览页部分接入成熟度模块

Book 概览页已经有：成熟度进度条、结构任务卡片、“最近事件”列表；
增加了通过 maturity snapshot 驱动的 Hook 和组件（use…Snapshot + NextStepsChecklist），能展示来自后端的任务/分值，而不是完全前端硬编码。
数据库与迁移脚本对齐

与 maturity 有关的迁移（特别是新表和字段）已经在 WSL2 上跑通，确认不会因为缺列/缺表导致 API 500；
老迁移中与已有结构冲突的部分（比如重复建表、重复加列）已经识别出来，不再盲目整包执行。
文档 / 设计层面同步

Plan98 已写成一份比较完整的设计说明（你现在打开的 Plan100 也引用了这部分）；
ADR-113 草案和 DDD / HEXAGONAL / VISUAL 三份 RULES 中，都已经有“成熟度独立模块化”的描述和当前实现快照（状态基本是 Accepted + 初步 Implemented）。
二、Plan100 中还没做完 / 进行中的部分

“只读 + 建议”改造还没彻底完成

仍有部分 UseCase（例如某些 book/block/todo 的更新）在“顺手重算成熟度”，而不是简化为 fire-and-forget 调用 maturity 模块；
还需要再过一轮，把所有会影响成熟度的写操作统一改成：业务成功优先，成熟度计算失败不影响主流程。
前端还没有 100% 切到 /maturity

概览页的主要视图已经接入 snapshot，但：
仍然存在基于 Book.maturity_score 或本地常量的逻辑（例如按钮阈值、部分结构任务的完成条件推断）；
需要继续收口：进度条 / 任务列表 / “40 分阈值 + 60 分可调区间”全都只用 snapshot 里返回的字段。
测试与降级策略补齐不足

maturity rule engine 和 /maturity router 目前还缺成体系的单元 / 集成测试；
对于 maturity 模块出错或 DB 不可用的场景，还没有一套明确的“降级 payload + 前端回退”策略落到代码里。
旧字段清理与长远减负还未开始实质拆除

代码中仍有不少地方直接读写 Book.maturity_score / Book.maturity / legacy_flag；
虽然现在不一定阻塞功能，但从 Plan100 的目标来看，这一批地方还需要标记 + 分批迁移到 snapshot / 建议式接口。
Plan98 / ADR-113 的“执行进度快照”尚未正式写入

Plan98 文档里你已经有文字描述（刚贴的这一段）；
还没有在文档末尾用“已完成 / 进行中 / 待办”清晰标记每一项，也没有在 ADR-113 中把端点路径、依赖关系和当前实现状态写完整。
如果你愿意，下一步我可以按 Plan100 里列的优先级，真的开始做两件事：
1）把 Book 概览页所有 maturity 相关视图统一改成只读 /maturity snapshot；
2）逐个排查后端“自动重算”入口，改成不影响主业务的 fire-and-forget，用几条测试保障不再“改算法就全站抖”。