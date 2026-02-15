---
id: ISS-LIB-TAGS-CLEAR
title: 清空 Tags 后卡片仍保留旧标签
status: closed
created_at: 2025-12-18
resolved_at: 2025-12-19
related_checks:
  - LIB-OVW-TagsPlaceholder
---

## 背景

在 Library 编辑弹窗中移除所有标签并保存后，Overview Grid/List 仍显示之前的标签（例如 `DEV`），导致 `LIB-OVW-TagsPlaceholder` 回归项失败。截图 2（编辑表单）与截图 3（卡片）可复现该问题。

## 影响

- UI 与后端状态不一致，用户误以为标签未被删除。
- “— No tags” 占位无法呈现，破坏信息架构。

## 解决方案

- `LibraryMainWidget` 在 tags 替换 API 返回空数组时，也同步更新 React Query / localStorage 缓存，确保前端立即反映空列表。
- 回归清单增加“无 Tags 显示占位”描述，ck-run 结果与 issue 关联。

## 状态

- 2025-12-18：首个修复方案已合并，但实测仍可复现（prefill 未加载时不会调用替换）。
- 2025-12-19：调整 `LibraryMainWidget`，基于 `editingLibrary.tag_total_count` 计算 `previousTagCount`，确保清空标签也会调用 replace API。新增 Playwright 用例覆盖 `LIB-OVW-TagsPlaceholder`。
- 2025-12-19：二次验证（含 `useQuickUpdateLibrary` 保留 tags 缓存的改动），在 ck-run-libraries-overview-2025-12-19-02 中标签相关检查通过，状态保持 closed。
