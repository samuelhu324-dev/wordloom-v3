---
id: ck-run-libraries-overview-2025-12-19-02
checklist_id: ck-libraries-overview-regression
date: 2025-12-19
version: v0.3.1
executor: self
result: failed
---

## 总结

- 基于当前 `ck-libraries-overview-regression` 执行手动回归。
- Tags 清空/更新后可即时刷新（`LIB-OVW-TagsRealtime` 通过，`ISS-LIB-TAGS-CLEAR` 已验证）。
- 发现 2 个新增回归 + 1 个沿存问题，见下方失败项。
- `LIB-OVW-CoverCrop`、`LIB-OVW-DeleteGone` 依然视为未实现（N/A）。

## 失败项

- [ ] `LIB-OVW-CoverViewTogglePersist` — 插入/更新封面图后，Grid ↔ List 切换会短暂回退到旧封面/空白；硬刷新后才恢复为最新封面。
- [ ] `LIB-OVW-PinArchiveRealtime` — Pin/Unpin 或 Archive/Restore 后，列表分组/徽标未即时刷新，需要硬刷新。
- [ ] `LIB-OVW-PinArchivedOrdering` — Archived 分组中 Pin 后未立刻排到分组最前，硬刷新后顺序才正确。

## 通过项（选摘）

- `LIB-OVW-TagsRealtime` / `LIB-OVW-EditPersists` / `LIB-OVW-TagsPlaceholder` 均通过。
- `LIB-OVW-CreateVisible`、`LIB-OVW-SearchWorks`、`LIB-OVW-StatusFiltersWork`、`LIB-OVW-BasementLinkWorks`、`LIB-OVW-StatusMetaAccurate` 正常。

## N/A / 未实现

- `LIB-OVW-CoverCrop` — 裁剪策略待新规范。
- `LIB-OVW-DeleteGone` — Library 软删除 + Basement 恢复尚未实现。
