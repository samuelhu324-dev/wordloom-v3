---
title: ADR-089 Plan_33 Paragraph Style & Hanging Indent Strategy
status: Accepted
date: 2025-11-22
tags: block, editor, paragraph-style, frontend, ddd, plan33
---

# 决策摘要
Plan_33 的“段落样式 / 悬挂缩进”需求通过 **ParagraphStyle 枚举** 实现：TextBlock 仍是原有聚合类型，仅在 metadata/DTO 中新增 `paragraph_style` 字段（`normal`、`ordered_list_item`、`bullet_list_item`、`definition_item`）。前端 BlockEditor 根据该枚举渲染 `<ol><li>` 或 `padding-left + text-indent` 悬挂缩进，同时提供工具栏按钮与快捷键（`1.` / `（1` + 空格、Tab/Shift+Tab、Shift+Enter）切换样式。**不创建新的 BlockType，也不硬编码空格缩进。**

# 背景问题
* Plan_33 要求在日志/Plan 模板里输入如下条目：
  ```
  Plan_28_LibraryDescription ✅
    （1 视图：……）
    （2 理由：……换行继续）
  ```
  关键是第二行之后要与“（1”对齐，属于列表/说明样式而非新语义。
* 旧 Block 模型只区分 BlockType，缺少段落样式信息，导致：
  - 只能靠手工空格或 Markdown hack，对齐脆弱。
  - UI 无法提供一键切换或快捷键体验。
  - 若为此新增 BlockType，将污染 Domain（因为“悬挂条目”没有独立语义）。

# 目标
1. 将“悬挂缩进”视为展示样式，保持 Domain 语义不变。
2. 提供可扩展的 ParagraphStyle 枚举，未来可追加更多样式。
3. 允许前端快捷键/按钮切换样式，支持 ordered/definition 两种典型布局。
4. 渲染保持可访问性（列表角色、aria-label），禁止依赖手敲空格。

# 方案细节
| Concern | 决策 | 说明 |
|---------|------|------|
| Domain 建模 | `ParagraphStyle` Enum (`normal`, `ordered_list_item`, `bullet_list_item`, `definition_item`) | 存储在 `Block.metadata.paragraph_style`，默认 `normal`。非法值抛 `BLOCK_INVALID_PARAGRAPH_STYLE`。 |
| DTO / API | `BlockResponse`、`BlockCreate/UpdateRequest` 增加 `paragraph_style` 可选字段 | 与 Enum 名称保持一致（小写 snake case）；若未提供返回 `normal`。 |
| 数据库存储 | `blocks.metadata` JSONB 新增 `paragraph_style` 键 | Migration 追加默认值 `"normal"`；查询时 fallback。 |
| 前端编辑器 | BlockEditor 工具栏添加 “悬挂条目” 切换；快捷键 `1.` / `（1`+空格自动启用 ordered；Tab/Shift+Tab 控层级；Shift+Enter 在同条内换行 | 渲染 `<ol><li>` 或 `padding-left:2em; text-indent:-2em`。Definition 样式固定 6ch 标签列。 |
| 导出/呈现 | 渲染层负责编号/标签；Domain 只存纯文本 | Markdown/Chronicle 输出时根据 paragraph_style 添加 `1.` / `：` 等标记。 |

## 交互约束
* 切换样式只更新 paragraph_style，不复制 Block 或改 type。
* Definition 样式分两列：`label`（行首“视图：”）使用 `text-indent` 与 `::before` 提供对齐。
* 列表条目 role 使用 `<ol role="list">`，每个条目 `<li role="listitem">`，保持可访问性。
* Placeholder 提示 “切换悬挂条目以书写 Plan_33 梳理”。

# 非目标
* 不引入 ParagraphBlock/PlanBlock 等新 BlockType。
* 不在 Domain 内解析/渲染编号文本；编号保持纯文本（由编辑器插入）。
* 不在本决策中实现完整富文本系统（仍限 TextBlock + 样式枚举）。

# 备选方案
| 方案 | 结果 | 理由 |
|------|------|------|
| 新增 `PlanItemBlock` 聚合 | 否 | 语义与 TextBlock 重叠、迁移成本大、会污染 BlockType Enum。 |
| 继续依赖手动空格/字符 | 否 | 不可维护、移动端输入困难、渲染/导出无法复现。 |
| 直接用 Markdown 列表语法 | 否 | Markdown->Slate Round-trip 不稳定，且 definition 样式无法用标准 Markdown 表达。 |

# 影响
* **DDD_RULES.yaml** 新增 `POLICY-016-PARAGRAPH-STYLE-PLAN33`，明确 ParagraphStyle 枚举与 API 契约。
* **VISUAL_RULES.yaml** `RULE_BLOCK_PARAGRAPH_STYLE_PLAN33` 约定 UI 交互与样式实现。
* Block API 在所有 CRUD 与列表响应中携带 `paragraph_style`。
* 将来导出/Chronicle 根据枚举决定 Markdown/HTML 结构。

# 实施步骤
1. 添加 `ParagraphStyle` Enum + Domain 校验（backend/api/app/modules/block/domain/paragraph_style.py）。
2. Migration：blocks.metadata JSONB 默认写入 `{"paragraph_style":"normal"}`；历史记录批量 backfill。
3. DTO / Schemas / Router 更新（请求 + 响应 +验证）。
4. 前端 BlockEditor 加入 toolbar 按钮、快捷键和 CSS 悬挂缩进。
5. 文档与测试同步（本 ADR + VISUAL_RULES + DDD_RULES + 单元/端到端测试）。

# 状态
Accepted – 文档已同步，后端/前端实现按上步骤推进；Plan_33 相关 UI 需求以此为准。

# 参考
* `assets/docs/QuickLog/D39-42- WordloomDev/Plan_33_ParagraphStyle.md`
* `assets/docs/DDD_RULES.yaml` → `POLICY-016-PARAGRAPH-STYLE-PLAN33`
* `assets/docs/VISUAL_RULES.yaml` → `RULE_BLOCK_PARAGRAPH_STYLE_PLAN33`
