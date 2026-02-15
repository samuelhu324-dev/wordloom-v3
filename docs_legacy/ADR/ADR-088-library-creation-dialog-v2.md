---
title: ADR-088 Library Creation Dialog V2 (居中弹窗重构)
status: Accepted
date: 2025-11-22
tags: frontend, ui, library, modal, ux, accessibility
---

# 决策摘要
将原有左侧“半屏灰板”式 Library 新建/编辑界面，重构为统一的居中弹窗 (Modal) 模式；创建与编辑共用同一组件，改善视觉成熟度、一致性与可访问性，减少视觉重量并强化仪式感。

# 背景问题
旧实现存在以下 UX / 视觉缺陷：
1. 占位过大：仅两个字段却占用整块高灰背景，信息密度低。
2. 结构不标准：像侧栏又像未对齐的弹窗，不符合常见产品模式 (Notion / Figma / Drive)。
3. 按钮节奏异常：主按钮位于左侧靠下，与全站右下或右侧主行动不一致。
4. 语义不清：标题 “New” / “Create Library” 与右上入口文案不统一。
5. 访问性不足：无初始焦点、ESC 不可关闭、遮罩不提供语义。
6. 创建成功缺少正向反馈，失败清空输入影响重试。

# 目标
提供“成熟产品范”创建/编辑体验：
* 统一交互：创建与编辑共用一个 `LibraryForm` + `Modal`。
* 视觉精简：固定宽度 480px，自适应 ≤92% 视窗；背景半透明保留上下文。
* 明确文案：中文优先；副标题引导用途。
* 一致行动区：右下角 Cancel（次要） + Create/Save（主色）。
* 访问性：自动聚焦 Name、ESC 与遮罩关闭、`role="dialog" aria-modal="true"`。
* 反馈：成功 toast + 新建卡片轻微高亮脉冲；失败 toast + 保留输入。
* 国际化准备：副标题 & 占位符文案集中在组件中，后续可抽出词典。

# 方案细节
| 组件 | 变更 | 说明 |
|------|------|------|
| `Modal` | 支持 `subtitle` | 增加副标题段落、精简样式、圆形关闭按钮、径向遮罩 + blur |
| `LibraryForm` | 模式 `create`/`edit` | 根据模式修改标题/按钮文案；Description 改 textarea；添加成功 toast |
| `LibraryMainWidget` | 状态 `highlightedId` | 新建成功后记录新库 ID，高亮 800ms 后清除；ESC 监听关闭弹窗 |
| `LibraryList` / `LibraryCard` | 高亮 class | 传入 `highlightedLibraryId` 匹配时添加动画样式 |

### 文案（中文优先）
* 标题：新建书库 / 编辑书库
* 副标题（新建）：为你的知识空间取个名字，稍后仍可修改。
* 副标题（编辑）：更新名称或简介，稍后仍可修改。
* Name 占位符：给书库起个名字…
* Description 占位符：比如：翻译项目、论文阅读、工作日报…
* 按钮：创建 / 保存 / 取消 / + New Library

### 高亮反馈
CSS `.highlighted`：外框柔和颜色脉冲 0.55s，强调新建成功，不打断布局。动画后回落到正常阴影。

### 错误处理
* Mutation 抛错时：读取 `error.message`（或后端链）展示 toast：“保存失败：<detail>”。
* 不清空表单；用户可直接修改继续重试。

### 可访问性
* `Modal` 添加 `role="dialog" aria-modal="true"`。
* 初始焦点：Name 输入框 `autoFocus`。
* 键盘：ESC 关闭；Tab 顺序：Name → Description → Cancel → Create/Save → Close（仍需后续焦点陷阱增强）。
* 颜色对比：按钮与文本遵循主题变量，满足 WCAG AA（蓝主色对比度 >4.5）。

### 非功能影响
* Domain / 后端不变：仅 UI 层重构；创建使用 POST /libraries，编辑使用 PATCH /libraries/{id}（由 quickUpdateMutation 驱动）。
* 与 DDD / Hexagonal 一致：无聚合结构变化，不引入新的 Port。

# 备选方案评估
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 保留侧栏 | 改动小 | 体验不成熟、空间浪费 | 否 |
| 全屏覆盖 | 仪式感强 | 过度遮挡上下文、仅两字段显臃肿 | 否 |
| 居中标准弹窗 (采用) | 成熟范式、上下文保留、可扩展 | 需统一样式、改动若干组件 | ✅ |

# 实施结果
提交包含：`Modal.tsx` / `Modal.module.css` 重构、`LibraryForm.tsx` 改造、`LibraryMainWidget.tsx` 托管状态与 ESC、`LibraryList.tsx` + `LibraryCard.tsx` 高亮支持、中文文案更新。

# 后续迭代 (Future Work)
1. 引入焦点陷阱与循环 (Focus Trap) 提升 A11y。
2. 抽离文案至 i18n 词典。
3. 表单错误行内提示（名称为空 / 后端校验冲突）。
4. 创建后滚动定位（若排序不在顶部，例如按名称排序时）。

# 决策状态
Accepted – 立即生效；同步 VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES 三处规则与策略。

# 变更日志
2025-11-22 初始版本。
