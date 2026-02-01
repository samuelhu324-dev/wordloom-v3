---
id: ISS-LIB-GROUPING-SIMPLIFY
title: Library Overview 分层精简为 All / Archived
status: closed
created_at: 2025-12-19
resolved_at: 2025-12-19
related_checks:
  - LIB-OVW-SectionPartitioned
  - LIB-OVW-PinArchiveRealtime
---

## 背景

原有分层为 Pinned / All / Archived，需求改为仅保留 All 与 Archived 两层，且 Pin/Archive 操作需即时在界面生效。

## 影响

- 分组展示与交互说明需要同步到回归清单与实现。
- Pin/Archive 未即时刷新会导致用户误判状态。

## 方案

- 前端移除 Pinned 分组，保留 All / Archived。
- 复用标签的缓存刷新思路：Pin/Archive 后立即写入 react-query 列表/详情缓存，确保界面即时反映；必要时再触发 invalidate 以与后端同步。

## 状态

- 2025-12-19：前端分层调整已提交，Pin/Archive 分组即时刷新验证通过，关闭。
