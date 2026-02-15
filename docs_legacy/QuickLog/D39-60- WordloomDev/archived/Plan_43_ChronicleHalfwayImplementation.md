当前完成概况

Phase 1 基础建模(任务1-7): 已完成。事件类型枚举、领域模型(ChronicleEvent)、仓储端口、Recorder/Query 服务草稿、表模型(chronicle_models.py)、迁移脚本 025_rebuild_chronicle_events.sql 已就位。
Phase 2 基础设施集成(任务8-13):
任务8 仓储实现: 已完成 SQLAlchemyChronicleRepository。
任务9 事件总线接入: 部分完成。已添加 chronicle_handler.py 订阅 BookCreated → 写入 BOOK_CREATED 事件；BlockStatusChanged 及其它事件尚未实现。
任务10 DI 注入: 已在 dependencies_real.py 中加入 get_chronicle_recorder_service / get_chronicle_query_service；Book 相关 UseCase 已改造支持 EventBus 发布事件。
任务11 路由: chronicle_router.py 已提供 POST /book-opened 与 GET /books/{id}/events。
任务12 跨域对接: Book 创建 / 移动 / 删除 / 恢复等事件现在通过改造的 UseCase 能触发事件总线；Chronicle 已录入 BookCreated。其它跨域事件（Block 状态变化）尚缺。
任务13 dependencies 完整性: Real 容器已更新；Mock/InMem 容器还未同步 Chronicle，属非关键未完成。
Phase 3 测试保障(任务14-16): 尚未开始。没有 Chronicle 专属 domain/repository/router/handler 测试用例。
Phase 4 优化与规则(任务17-19): 未开始。速率限制、防抖、性能基线与 RULES 三文件新增段落均未编写。
Phase 5 文档与交付(任务20-22): 未开始。ADR-093、未来工作列表、前端 Timeline UI 说明未落地。
已额外完成的改造

CreateBookUseCase / DeleteBookUseCase / MoveBookUseCase / RestoreBookUseCase / UpdateBookUseCase 增加可选 EventBus，支持把聚合根事件发布出去。
事件发布后清理聚合事件队列，避免重复。
主应用启动已确保导入 infra.event_bus.handlers 触发注册。
尚未覆盖的关键缺口

Chronicle 未记录 BookMoved / BookDeleted / BookRestored / BlocksUpdated / BlockCreated 等更多事件（需决定哪些进入最小集，再补 handler）。
BlockStatusChanged 枚举对应事件触发链条尚未落地；Block 模块当前没有状态变更事件适配 Chronicle。
没有分页/查询测试来验证 list_book_events 返回顺序与总数。
RULES 文件 (DDD / HEXAGONAL / VISUAL) 未新增 Chronicle 段落。
ADR-093 未创建。
前端未添加时间线组件 / API 调用集成（仅后端接口存在）。
速率限制与防抖 TODO 未实现（book-opened 可能被刷写）。
风险与注意

若大量 BookOpened 频繁写入，单表可能快速膨胀（短期可接受但需后续限流）。
缺少测试会导致后续扩展时易回归破坏事件顺序或索引假设。
尚未定义 payload 版本策略，后续扩展字段需 ADR 约束。
建议下一步优先序

扩展事件处理：实现 BookMoved / BookDeleted / BookRestored → Chronicle （是否都需要可先在 ADR 中界定最小集合）。
为 Block 增加一个简单状态/内容变化事件到 Chronicle（若近期就要观察 Block 活动）。
编写最小测试：
Repository 保存 + 查询分页顺序
Handler 触发（模拟 BookCreated 发布后 chronicle_events 有记录）
Router GET /books/{id}/events 排序与分页
起草 ADR-093（先最小骨架，后补细节）→ 与 RULES 三文件同步引用。
添加 RULES 新段落 (Domain 6 / module_chronicle / timeline_ui)。
前端添加基础时间线请求 hook + 简单列表组件（不做聚合）。
再评估速率限制与后续 BlockStatusChanged/Focus 事件的接入窗口。
可选快速里程碑定义

M1（当前）：事件表 + BookCreated 写入 + 基础查询。
M2：更多 Book 事件 + 基础测试 + ADR 草稿。
M3：Block 事件 + RULES 更新 + 前端时间线初版。
M4：限流/防抖 + 未来统计投影设计基线。
需要我直接开始第 1 步（补更多 handlers + 最小测试）吗？或先写 ADR 草稿？告诉我优先方向即可。