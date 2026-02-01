---
id: ck-run-libraries-overview-2025-12-19-01
checklist_id: ck-libraries-overview-regression
date: 2025-12-19
version: v0.3.0
executor: self
result: failed
---

## 总结

- 依据更新后的 `ck-libraries-overview-regression` 执行手动回归。
- 核心流程、Pinned/Archived 分层、Basement CTA、搜索（Title + Description）均通过。
- 仍有 1 个阻塞项：清空 Tags 后卡片仍显示旧标签（缓存未清除）。
- `LIB-OVW-CoverCrop`、`LIB-OVW-DeleteGone` 仍属未来能力，本轮记为 N/A。

## 失败项

- [ ] `LIB-OVW-TagsPlaceholder` — “— No tags” 占位未生效
  - 复现：编辑 Library → 删除所有 Tags → 保存；Grid/List 仍显示旧标签（如 `LAB`）。
  - 影响：用户无法确认标签是否被清空，ck 回归项失败。
  - ISSUE：[#ISS-LIB-TAGS-CLEAR](../issues/ISS-LIB-TAGS-CLEAR.md)（已再次打开，等待缓存剔除方案验证）。

## N/A / 未实现

- `LIB-OVW-CoverCrop` — 裁剪策略待新规范，参考 [#ISS-LIB-COVER-RATIO](../issues/ISS-LIB-COVER-RATIO-cropping-rules.md)。
- `LIB-OVW-DeleteGone` — Library 软删除 + Basement 恢复待规划，参考 [#ISS-LIB-DELETE](../issues/ISS-LIB-DELETE-library-level-delete.md)。

## 备注

- 新增检查 `LIB-OVW-BasementBookshelfDefault`：创建 Library 后状态栏书架数应至少为 1（Basement）。本轮创建记录符合预期，后续仍需保持关注。
