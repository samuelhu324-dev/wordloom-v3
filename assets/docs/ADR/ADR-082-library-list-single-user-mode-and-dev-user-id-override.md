# ADR-082: Library List Single-User Mode & DEV_USER_ID Override

Date: 2025-11-21
Status: Accepted
Authors: Backend / Frontend / Architecture
Supersedes: (None) – Clarifies multi-library roadmap from ADR-071
Related: DDD_RULES v3.10, HEXAGONAL_RULES v1.9, VISUAL_RULES v2.6

## Context
原设计遵循多用户 + 每用户多 Library 模式，`GET /api/v1/libraries` 通过依赖 `get_current_user_id()` 过滤。开发阶段出现以下问题：
1. 固定 Stub UUID (`550e8400-e29b-41d4-a716-446655440000`) 与数据库历史数据的 `user_id` 不匹配，导致返回空列表。
2. Router 旧实现在异常（数据库/会话）时捕获后直接返回 `[]`，前端无法区分“真实空”与“失败”。
3. 调试流程复杂：需要伪造或迁移库的 `user_id` 才能看到数据。
4. 单人开发阶段暂未引入权限/多租户；过滤带来的复杂度暂不产生价值。

## Forces / Drivers
- 优先恢复可见性：库数据需立即呈现，便于继续上层 Bookshelf / Book 流程。
- 降低调试成本：去除隐藏错误的 silent-empty 行为，提供诊断信息。
- 保持可逆：未来进入多用户阶段可以无痛恢复过滤逻辑。
- 不牺牲代码质量：保留结构化端口/适配器，增加最小增量。

## Decision
进入“单用户列出模式”：`GET /api/v1/libraries` 改为不按 `user_id` 过滤，返回全部库。新增诊断与环境覆盖：
- Repository 新增 `list_all()` 方法。
- Router `list_libraries` 调用 `list_all()`；异常抛出 `HTTPException(500)`（不再 silent）。
- 支持 `?debug=true` 返回头部：`X-Debug-Library-Count`。
- 新增调试端点：`/api/v1/libraries/debug/meta`（count + has_libraries），`/api/v1/libraries/debug/all`（完整列表）。
- `security.get_current_user_id` 支持环境变量 `DEV_USER_ID` 覆盖（为后续恢复过滤预留）。

## Implementation Summary
Backend:
- `infra/storage/library_repository_impl.py`：添加 `list_all()`。
- `library_router.py`：重写 `list_libraries`（去过滤 + debug headers + 500 错误暴露）；新增 `debug/meta` 与简化 `debug/all`。
- `security.py`：`get_current_user_id()` 读取 `DEV_USER_ID` 环境变量，非法格式回退默认 UUID。
Frontend:
- 无需变更调用层（仍使用 `GET /libraries`）。
- 可选：在空列表时读取 `X-Debug-Library-Count` 区分“真空 vs 错误”（后续增强）。
Documentation:
- 三个 RULES 文件版本升级并添加单用户模式与调试端点说明。

## Alternatives Considered
1. 直接迁移所有库记录的 `user_id` 为 Stub：侵入数据、未来切换多用户需再次迁移。
2. 保留过滤但暴露错误：仍需人工对齐 `user_id`，调试成本高。
3. 引入 JWT & 多用户验证：当前阶段过早，增加配置与依赖。

## Consequences
Positive:
- 库数据立即可见，排除“看不到历史数据”的阻碍。
- 错误不再伪装成空列表，前端可明确诊断。
- 最小改动保持可逆性：恢复过滤只需改回调用 `list_by_user_id`。
Trade-offs:
- 暂时失去用户隔离；所有库在单端点暴露（仅开发环境）。
- 需要后续 ADR 重新引入鉴权与访问控制（多租户阶段）。

## Rollback Plan
当进入多用户阶段：
1. 将 `list_libraries` 改为调用 `list_by_user_id(user_id)`。
2. 保留或参数化 debug headers；`/debug/all` 端点删除或加鉴权。
3. 编写迁移脚本统一现有库的 `user_id`（若需要）。

## Future Work
- ADR（计划）：“Library Multi-Tenant Reinstate & Authorization Middleware”。
- 前端：空状态区分（真实空 vs 500）显示不同信息与重试按钮。
- 监控：记录 500 与 count=0 访问频率，评估何时恢复过滤。

## Status Links
- DDD_RULES v3.10: 更新 `frontend_libraries_endpoint_status` & changelog。
- HEXAGONAL_RULES v1.9: 新增 `library_listing_mode` 部分。
- VISUAL_RULES v2.6: 更新前端端点状态 + API client 文档。

## Decision Record
Accepted: 2025-11-21. Active until multi-user authentication introduced.

## References
- Original multi-library flat routing: ADR-071
- Async repository migration: ADR-069
- Block inline editor change (context for simultaneous UX simplification): ADR-081
- Source commits Nov 21, 2025 (library router + security overrides)
