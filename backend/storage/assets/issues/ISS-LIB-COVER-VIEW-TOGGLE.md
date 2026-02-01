---
id: ISS-LIB-COVER-VIEW-TOGGLE
title: 封面更新后在 Grid/List 切换时丢失或回退
status: closed
created_at: 2025-12-19
resolved_at: 2025-12-19
related_checks:
  - LIB-OVW-CoverViewTogglePersist
---

## 背景

在 Library Overview 中上传/更新封面后，切换 Grid ↔ List 视图会短暂回退到旧封面或空白，硬刷新后才恢复为最新封面。

## 影响

- 封面状态与用户预期不一致，影响视觉确认。
- 回归项 `LIB-OVW-CoverViewTogglePersist` 失败。

## 解决方案（实施中）

- 上传封面成功后，立即将新封面写入 react-query 所有 `['libraries', ...]` 列表缓存、详情缓存，以及 `wl_libraries_cache`，避免后续旧列表响应覆盖。

## 状态

- 2025-12-19：已提交前端缓存修复，回归验证封面在视图切换后保持最新，故关闭。
