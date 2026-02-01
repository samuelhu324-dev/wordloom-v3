# ADR-087: Library 封面双规格与列表头像策略

Date: 2025-11-22
Status: Accepted
Authors: Frontend / Product / Architecture
Supersedes: (None)
Related: DDD_RULES v3.11 (草拟), HEXAGONAL_RULES v1.10 (草拟), VISUAL_RULES v2.7 (草拟), Plan_23_LibraryPreviewGallery

## Context
- Library 列表存在两种场景：
  - 大厅卡片（参见附件截图 2）以 16:9 横幅展示，需要高清封面保持沉浸感。
  - 横向密集列表（附件截图 1）主要用于管理和比对，缺少视觉锚点，难以凭封面记忆快速识别。
- 现有数据模型仅提供 `cover_media_id`，前端统一通过 `buildMediaFileUrl` 拉取原始图；无缩略图区分，导致列表如果直接使用同一图片会加载过大资源。
- Plan_23 提出「大厅级封面不要用 thumb」的设计建议，即：保持大卡片使用高清横幅，同时为列表/小组件提供独立的小尺寸头像，避免糊图与带宽浪费。
- 需要在不破坏 Hexagonal/DDD 边界的前提下交付列表头像，同时预留未来引入后台缩略图的演进路径。

## Forces / Drivers
- **视觉识别**：列表视图需要一个稳定的小型封面，帮助用户在文本密集的行内快速定位。
- **带宽/性能**：列表可能一次加载数十条库；若直接拉取 1000px+ 横幅会浪费带宽并影响首屏。
- **一致性**：大卡片与列表应共享同一封面来源，更新时立即反映，避免两个视图出现不同步图像。
- **架构边界**：Library 聚合保持轻量，不希望新增多个封面字段；缩略图生成应归属 Media 模块。
- **计划演进**：Plan_23 明确 Phase A（CSS 缩放 + 渐变占位）与 Phase B（后端缩略图端点），需要在决策中锁定演进路线。

## Decision
采纳双规格封面策略：
1. **Phase A（当前交付）**
   - 继续复用 `cover_media_id` → `buildMediaFileUrl(media_id, updated_at)` 生成 `coverUrl`。
   - Library 卡片维持 16:9 横幅；新增列表头像组件 `LibraryCoverAvatar`，使用 32px 方形容器，`object-fit: cover` 缩放原图，并将 `loading="lazy"` 作为默认参数控制加载。
   - 无封面场景复用 deterministic 渐变背景（`coverGradientFromId`）+ 首字母占位，保证列表行高度对齐。
   - 设计 Token `--library-avatar-size: 32px`，统一头像尺寸，列表 grid 布局首列专用于头像。
2. **Phase B（未来演进）**
   - 预留 Media 适配层 `IMediaRepository.get_thumbnail(media_id, size)` 与 REST 端点 `/media/{id}/thumbnail?size=32`。
   - 当前组件仅需在实现后切换 `coverUrl` 的来源即可，无需改动列表布局。

## Implementation Summary
Frontend:
- 新增 `LibraryCoverAvatar` 组件（32px 圆角方块，lazy image + 渐变占位）。
- `LibraryList` list 模式 grid 模板改为 `avatar + 名称 + 说明 + #Books + 创建时间 + 操作`，并依赖新的 Token 控制列宽。
- `LibraryCard` 提取 `coverGradientFromId` 工具，保持卡片封面与头像梯度一致。
- 设计 Token `--library-avatar-size` 定义在 `shared/styles/tokens.css`。

Documentation:
- `DDD_RULES.yaml` 新增 `POLICY-LIBRARY-COVER-AVATAR` 记录两规格策略与 Phase A/B。
- `HEXAGONAL_RULES.yaml` 添加 `library_cover_avatar_strategy`，描述端口/适配器对齐与性能注意事项。
- `VISUAL_RULES.yaml` 新增 `RULE_LIB_OVERVIEW_COVER_AVATAR`，定义列表头像实现细节与未来切换指引。

## Alternatives Considered
1. **继续只用横幅**：列表直接缩放原图。结论：列表加载冗余资源、视觉过度；否决。
2. **后端立即实现缩略图**：同步交付 thumbnail 端点。现阶段时间紧，且 Media 模块尚无缩放 pipeline；先采用 CSS 缩放，后续再扩展。
3. **新增 `cover_thumb_media_id` 字段**：领域层直接维护两份媒资。会增加同步复杂度与一致性压力，违反当前聚合最小化原则；暂缓。

## Consequences
Positive:
- 列表视图拥有明确封面锚点，提升辨识度。
- 大卡片与列表共享同一媒资，更新后立即写入 `updated_at`，避免缓存陈旧。
- 文档与规则同步，便于团队共识。

Trade-offs:
- Phase A 仍需加载原图；但列表头像尺寸固定、懒加载，可在后续替换为真实缩略图以彻底优化。
- 需关注极端环境下的加载顺序（大量库 + 低网速），必要时结合虚拟滚动或预加载策略。

## Rollback Plan
- 若头像导致性能或视觉问题，可通过 Feature Flag 退回旧列表（移除 avatar 列、恢复原 grid 模板）。
- 删除 `LibraryCoverAvatar` 使用点，撤回 Token 与规则条目；无需数据库回滚。

## Future Work
- 实现 Media thumbnail 端点 + CDN 缓存策略，使列表加载 32px 缩略图。
- 设计 “上传时自动生成多规格” pipeline，并在 `uploadLibraryCover` 成功后回传各规格 URL。
- 结合 Plan_23 的滤镜建议，为大卡片封面增加统一色调与模糊层，保证审美一致性。
- 当库数量 >100 时，评估引入虚拟滚动与懒加载占位骨架，避免一次加载过多图像。

Accepted: 2025-11-22.
