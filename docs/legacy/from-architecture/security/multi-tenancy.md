# Multi-tenancy

## Phase 0

- 以 Library owner 作为隔离边界。
- Search 投影的 scope key 先用 `library_id`（与未来 tenant/workspace 演进兼容）。

## Phase 1+

- 引入 tenant/workspace 表
- API：actor -> tenant scope
- DB：强制按 tenant scope 过滤/约束（必要时加 FK/partial index）
