# ADR-070: 书架封面与默认 Library 策略（Phase A → Phase B）

- Status: Accepted
- Date: 2025-11-17
- Owners: Platform (Frontend + Backend)
- Related: DDD_RULES.yaml (POLICY-011), HEXAGONAL_RULES.yaml (ui_integration_guidelines.bookshelf_cover), VISUAL_RULES.yaml (RULE_BS_ILLUSTRATION_BUTTON/RULE_BS_COVER_STRATEGY)

## 背景（Context）
- 需求：在“书架预览页右上角增加插图悬浮按钮”，点击设置/插入封面；风格参照截图卡片（标题、描述、封面）。
- 约束：
  - DDD/Hexagonal：Bookshelf 聚合不包含封面字段（cover/cover_url）。封面属于媒资（Media）领域，应通过关联解耦。
  - 当前后端 Router 已就绪，未内嵌封面解析逻辑；Media 模块已具备上传与关联接口（associate/disassociate）。
- 目标：先以“前端无后端依赖”的方式快速上线；随后演进到“媒资关联 + 便捷 API”的持久化方案。

## 决策（Decision）
采用“两阶段策略”以兼顾交付速度与架构一致性：

1) Phase A（前端本地，立即可用）
- 交互：书架详情页右上角提供“插图”悬浮按钮；点击弹出对话框，输入 https:// 图片 URL 并预览。
- 存储：前端 localStorage，键为 `bookshelf:cover:{bookshelfId}`。
- 优先级：显式封面（localStorage） > 占位图。
- 范围：不改动后端 Domain/Repository/Router。

2) Phase B（媒资关联，后端持久化）
- 关联：使用 MediaAssociation(entity_type=bookshelf, entity_id) 绑定一张主图作为封面。
- API 合约：
  - 列表实体媒资：`GET /api/v1/media/{entity_type}/{entity_id}`
  - 关联：`POST /api/v1/media/{media_id}/associate?entity_type=bookshelf&entity_id={uuid}`
  - 解除：`DELETE /api/v1/media/{media_id}/disassociate?entity_type=bookshelf&entity_id={uuid}`
- UI 优先级：显式封面（用户设置） > 关联媒资主图 > 占位图。
- 可选增强：在 Bookshelf list/detail 的 HTTP 适配层拼装 `cover_url` 字段（仅 Router 层，不入 Domain/Repository）。

此决策确保：
- 与 DDD/Hexagonal 保持一致（封面不进入聚合，不污染端口/适配器边界）。
- 先交付 UI 能力（Phase A），后续平滑迁移到后端持久化（Phase B）。

## 方案细节（Details）

### Frontend（已落地 Phase A）
- 组件：
  - `frontend/src/features/bookshelf/ui/BookshelfHeader.tsx`（封面区 + 悬浮按钮 + 文本叠加）
  - `frontend/src/features/media/ui/ImageUrlDialog.tsx`（URL 对话框 + 预览 + 校验）
- 页面接入：
  - `frontend/src/app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/page.tsx`
- 存储键：`bookshelf:cover:{bookshelfId}`；占位图回退（Unsplash）。

### Backend（Phase B 对齐）
- 已有：Media 模块（上传、关联、回收站、清理）。
- 关联形态：`MediaAssociation(entity_type=bookshelf, entity_id, media_id)`。
- 端点使用规范：见上文 API 合约。
- 便捷性（可选）：Router 在 list/detail 时拼装封面 `cover_url`，但不进入 Domain/Repository。

## 兼容性（Consequences）
- 正面：
  - Phase A 零后端改动，快速满足可视化需求。
  - Phase B 完全遵循端口与适配器分离，聚合边界干净，演进成本低。
- 负面/限制：
  - Phase A 封面仅本地生效（换设备不可见）；需尽快切到 Phase B。
  - Router 拼装 `cover_url` 仅限 HTTP 适配层，避免跨层泄漏。

## 迁移路径（Migration Plan）
1. 在 UI 中新增“从媒资库选择”入口（Phase B UI）。
2. 调用上传 + 关联端点，建立 entity=bookshelf 的主图关联。
3. 加载详情时并行请求 entity media，选择主图渲染；如无需多次请求，可在 Router 层拼装 `cover_url`（可选）。
4. 若存在 localStorage 封面，提示用户“一键迁移为持久封面”（创建媒资并关联）。

## 默认 Library 策略（Default Library）
- 保持 RULE-001（一用户一个 Library）。默认 Library 的创建策略不在本 ADR 内修改后端规则：
  - 若需要“首次登录自动创建 Library”的体验，可在应用层/路由器层提供“若无则创建”的流程（单点实现，尊重 Domain 约束）。
  - 与本 ADR 的封面策略无直接耦合，仅作为 UX 补充建议。

## 验收标准（Acceptance Criteria）
- Phase A：
  - 书架详情可通过悬浮按钮设置 URL 封面并即时显示；刷新后仍生效（localStorage）。
  - 无封面时使用占位图；按钮 hover 显隐符合视觉规范。
- Phase B：
  - 能从媒资库选择/上传图片并与书架建立关联；可解除关联。
  - UI 覆盖优先级：显式封面 > 关联主图 > 占位图。
  - 可选：列表/详情响应包含 `cover_url`（由 Router 拼装）。

## 备选方案（Alternatives Considered）
- 将 cover 直接加入 Bookshelf 聚合：
  - 否决。违反聚合边界，跨领域耦合，影响可扩展性与一致性。
- 仅在后端实现（拒绝 Phase A）：
  - 否决。降低交付速度；前端完全受阻于后端进度。

## 风险与缓解（Risks & Mitigations）
- Phase A 与 Phase B 的双轨可能导致 UI 分支复杂：
  - 缓解：抽象“封面提供器”接口，Phase A/B 仅替换实现。
- 媒资列表额外请求影响性能：
  - 缓解：并行请求 + 结果缓存；或在 Router 拼装 `cover_url`（仅适配层）。

## 实施状态（Implementation Status）
- Phase A：已完成（组件 + 页面接入 + 规则文档同步）。
- Phase B：待办（UI 入口、关联调用、可选的 Router cover_url 拼装）。
