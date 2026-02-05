# ADR-002: Auth Scope / Multi-tenancy (Phase 0)

## Context

- 目前没有 tenant/workspace 表。
- 需要先把隔离边界跑起来，避免越权。

## Decision

- Phase 0：以 Library owner（`library.user_id`）作为隔离边界。
- 业务用例入口统一做 owner-check；router 注入 Actor。

## Consequences

- 先把主链路 SoT“权限/隔离/约束/事务”打牢。
- 后续引入 tenant/workspace 时，把 scope key 从 owner 迁移到 tenant/workspace。
