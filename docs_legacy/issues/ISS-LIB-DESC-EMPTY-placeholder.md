---
id: ISS-LIB-DESC-EMPTY
title: Library 描述为空时缺少占位提示
status: closed
created_at: 2025-12-18
resolved_at: 2025-12-19
---

## 背景

当用户在 Library 表单中清空 Description 字段并保存，Grid/List 卡片上会出现完全空白的描述区域，未显示预期的 "— No description" 占位文本，导致页面看起来像是渲染故障。

## 预期

- Library Overview 所有视图（Grid / List / Horizontal）中，Description 为空或仅含空白字符时，统一展示 `libraries.list.description.empty` 对应的文案。
- Tooltip、title 属性、Screen Reader 描述也要同步 fallback，避免读出空字符串。
- 为该行为补充自动化或 checklist 覆盖（LIB-OVW-DescPlaceholder）。

## 备注

- 首次记录自 ck-run-libraries-overview-2025-12-18。

## 解决

- `LibraryTagsRow` / `LibraryCard` / List 视图统一在 description 为空或仅空白字符时回退到 `libraries.list.description.empty` 文案。
- Tooltip 和 `title` 属性也走同一 fallback，读屏不再朗读空字符串。
- `LIB-OVW-DescPlaceholder` 在 2025-12-19 的 ck-run 中标记通过，并准备后续自动化回归脚本。
