先列出 Chronicle 模块实施的分阶段待办任务清单。

Created 22 todos

以下是 Chronicle 模块的周全成熟实施计划（含策略、步骤与交付物），已拆分到待办列表，便于后续 agent 模式逐项执行。你可先审阅，有需要我再微调后开始动工。

总体目标

建立最小可用 Chronicle 事件系统：纯事件存储 + 基础查询，不做即时统计汇总。
仅绑定最小业务单元 Book（Block 可选），Bookshelf/Library 统计通过读侧聚合。
与现有六边形结构对齐：领域 → 端口 → 基础设施适配器 → 应用服务 → 路由。
首批事件：BookCreated（跨域）、BlockStatusChanged（跨域）、BookOpened（直接路由）、后续可扩展 FocusStarted / FocusEnded。
输出结构化 ADR（ADR-093）与三份 RULES 文件更新，保证规范溯源。
阶段划分

Phase 1 基础建模：任务 1-7（边界、模型、迁移）。
Phase 2 基础设施集成：任务 8-13（仓储实现、事件总线、依赖注入、路由）。
Phase 3 测试保障：任务 14-16（领域/仓储/API/事件总线）。
Phase 4 优化与规则更新：任务 17-19（性能、速率限制预留、规则文件补充）。
Phase 5 文档与交付：任务 20-22（ADR、对外说明、未来优化列表）。
关键设计要点

事件表 chronicle_events：单表存储全部事件；扩展靠 event_name + payload。
必备索引：btree(book_id, occurred_at), btree(event_name, occurred_at), 未来视查询加 GIN(payload) 可延后。
事件统一时间语义：occurred_at（业务发生时间）与 created_at（记录插入时间）。
应用服务分离写读：RecorderService (写) / QueryService (读)；后续可加 StatsProjectionJob。
跨域事件接入：通过 event_bus handler 转为 ChronicleEvent（保持解耦，不直接耦合其它聚合仓储）。
API 暂不暴露任意事件写入口，只开放 BookOpened 专用端点减少滥用。
速率限制与防抖：暂留 TODO（集中写入风险控制第 2 迭代处理）。
前端可视化：VISUAL_RULES 记录“时间线组件”约定（时序排序、事件类型标记、聚合延后策略）。
规则文件更新策略

DDD_RULES.yaml：补 Domain 6: Chronicle 章节（职责、事件列表、禁止直接统计字段、聚合策略说明）。
HEXAGONAL_RULES.yaml：新增 module_chronicle 节，明确端口 ChronicleRepositoryPort 与 Handler 角色。
VISUAL_RULES.yaml：新增 chronicle_timeline_ui 段，规定前端只请求分页事件、客户端聚合标签。
ADR-093 结构建议

Title & Status
Context（统计诉求 + 现有缺口）
Decision（事件最小化 + 仅 Book 主键 + 读侧聚合）
Architecture（端口、模型、事件总线、查询契约）
Data Model（表结构 + 索引 + 示例事件 JSON）
Non-Goals（不做实时汇总、不做复杂速率控制、暂不投影 stats）
Future Work（预计算、速率限制、payload schema versioning）
Alternatives Considered（直接在 book 表累加计数 vs 事件驱动）
Consequences（查询 join 成本按需优化）
测试重点

领域：非法空 book_id 拒绝；payload JSON 严格结构。
仓储：save 后查询一致；分页契约符合 Pagination V2（如果有）。
事件总线：模拟 BookCreated 触发，验证 Chronicle 记录。
API：BookOpened 去重策略暂不实现但预留 TODO；返回排序正确（occurred_at DESC）。
风险与缓解

写入量增长风险：后续分区或归档；当前预留 occurred_at 范围索引。
查询性能：限制默认分页大小；延迟大规模统计需求。
事件膨胀：ADR 规定 versioning + 必要字段最小化。
交付清单

新目录结构：backend/api/app/modules/chronicle/{domain,application,routers,schemas,__init__.py}
新文件：infra/database/models/chronicle_models.py, infra/storage/chronicle_repository_impl.py, 迁移脚本、事件处理器。
RULES 三文件补充段落。
assets/docs/ADR/ADR-093-chronicle-module-design.md
更新 QuickLog 关联引用（Plan40 → ADR-093）。
Basic tests + 运行说明。