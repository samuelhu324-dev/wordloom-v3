---
id: ISS-LIB-DELETE
title: 支持 Library 级删除（含软删策略）
status: open
created_at: 2025-12-18
---

## 背景

当前仅支持Book级删除，Library 本身无法删除

## 预期

- 提供 Library 级删除能力，优先软删
- 硬删会同时涉及到Bookshelf和Book与其中Blocks的综合删除问题，应提高处理权限与门槛

## 备注

- 首次记录自 ck-run-libraries-overview-2025-12-18。