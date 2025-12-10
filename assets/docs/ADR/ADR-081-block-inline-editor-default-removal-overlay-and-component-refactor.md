# ADR-081: Block Inline Editor Default Adoption & Overlay Removal

Date: 2025-11-21
Status: Accepted
Authors: Architecture / Domain / Frontend Teams
Supersedes: (None) – complements ADR-080
Related: ADR-080 (Rich Block Types & Plugin Architecture), DDD_RULES v3.9, HEXAGONAL_RULES v1.8, VISUAL_RULES v2.5

## Context
Phase 2 的 Block 编辑实现最初采用覆盖式 BlockEditor 组件（overlay/modal 风格），通过双击进入编辑态。近期在真实使用中暴露以下问题：
1. 交互成本高：需要双击进入与点击退出，阻断连续编辑流。
2. 上下文丢失：覆盖层遮挡其它块，用户难以保持段落相对位置感。
3. 技术不稳定：在块删除时，map 回调内声明的 hooks 数量变化，触发 React 错误 `Rendered fewer hooks than expected`。
4. 领域纯度：覆盖层推动了“进入编辑态”额外 UI 状态，但 Domain 本身无需感知这一态。
5. 扩展阻力：后续富类型插件（表格/代码/图片）若继续覆盖层模式，会重复渲染逻辑与状态管理。

## Forces / Drivers
- 用户体验（UX）需要“见即所得”编辑，无模式切换。
- 降低认知与实现复杂度，避免额外 Editor 状态机。
- 维持领域模型最小化（content 为纯字符串/JSON，不引入富文本 AST）。
- 减少错误点：稳定 hooks 顺序，避免 runtime hook mismatch。
- 为即将到来的插件体系 (ADR-080) 打好可插拔基础。

## Decision
采用“默认行内编辑”模式：每个 Block 在列表中直接以 textarea（或未来特定类型的编辑器组件）呈现并可立即修改。
- 移除旧覆盖式 `BlockEditor.tsx` 组件与双击进入逻辑。
- 提取 `BlockItem` 子组件：在其中封装 `useUpdateBlock` / 本地 `useState`，`BlockList` 仅 map 渲染，确保 hook 顺序稳定。
- 保存触发机制：`blur`、`Ctrl+S/Cmd+S`、`Enter(非 Shift)`；`Esc` 回滚未保存改动。
- 重排快捷键：`Alt+↑ / Alt+↓` 使用 Fractional Index 中值策略计算 `new_order`。
- Schema 对齐：migrations 014 (block_type→type), 015 (sort_key→order + heading_level + meta + Decimal 精度) 已应用并反映到前端与事件模型。
- 事件模型修复：`BlockCreated` 移除多余 `aggregate_id` 参数，统一 `block_id` + `aggregate_id` property。

## Status Impact
- DDD_RULES：新增 POLICY-BLOCK-INLINE-EDITING 与 POLICY-BLOCK-HOOK-STABILITY。
- HEXAGONAL_RULES：记录 inline 决策对端口/适配器简化的影响；减少 Application Layer 复杂度。
- VISUAL_RULES：新增 RULE_BLOCK_INLINE_EDITING_DEFAULT（样式、快捷键、触发条件、错误处理）。

## Alternatives Considered
1. 保留覆盖式编辑器 + 优化：仍存在上下文丢失与 hooks 不稳定问题，复杂度高。
2. 混合模式（预览 + 点击转编辑）：增加状态切换与分支逻辑，不利于后续插件统一。
3. 富文本库（Slate / ProseMirror）提前引入：过早引入重量级依赖，阻塞后端迭代；当前仅需纯文本。

## Consequences
Positive:
- 极简交互：打开页面即可编辑，减少 1~2 步操作。
- 更低认知负担：无“进入/退出”编辑态显式概念。
- 更稳定运行：删除块不再触发 hooks 重排错误。
- 领域保持纯净：无编辑态事件污染 Domain。
- 插件扩展路径统一：未来富类型沿用行内容器。
Trade-offs:
- 失去覆盖层带来的聚焦模式与大屏专注体验。
- textarea 在长内容 (>15KB) 下需要自动高度与拆分提示（后续 ADR 规划）。
- 暂无富格式工具栏；后续通过插件注册补齐。

## Implementation Notes
Frontend:
- 新文件：`BlockItem.tsx`（内部本地 state + mutation）。
- 更新文件：`BlockList.tsx`（移除编辑态切换，直接渲染 <BlockItem/>）。
- 样式升级：`BlockList.module.css` 添加 `.inlineTextarea` 渐变边框、focus ring、深色模式变体。
Backend:
- Migrations: 014, 015 已运行；`order`/`type` 字段与 ORM 同步；事件 dataclass 修正。
- 无需额外端点；现有 PATCH /blocks/{id} 满足行内保存。
Testing:
- 行内编辑可通过组件快照与输入模拟直接测试；去除覆盖层 mount/unmount 场景。
- 后续可添加性能测试：大量块渲染下的输入响应时间。

## Data Model & Ordering
- 继续使用 Decimal(36,18) Fractional Index；行内编辑不影响 `order`。
- 重排仅在快捷键或拖拽时计算新中值；避免全列表重写。

## Rollout Plan
- 已一次性切换：覆盖式组件删除后无法回退；若需临时回退，可通过 Git 历史恢复 `BlockEditor.tsx`。
- 监控：前端错误日志观察 24h；若出现性能瓶颈，临时限制最大同时渲染块数并引入虚拟化。

## Future Work
- ADR-082（计划）：自动高度 + 粘贴拆分策略。
- 插件扩展 (Dec 05)：富类型编辑器注册到 `blockPlugins`。
- 可访问性增强：ARIA 标注与键盘焦点路径说明面板。
- 性能：虚拟化/IntersectionObserver for large lists。

## Decision Record
Accepted on 2025-11-21; all相关规则文件与代码已同步（版本：DDD 3.9 / HEXAGONAL 1.8 / VISUAL 2.5）。

## References
- ADR-080-block-editor-integration-rich-block-types-media-plugin-architecture.md
- Migrations 014, 015
- React Error: Rendered fewer hooks than expected (resolved)
- Fractional Index Ordering Strategy Notes
