# AuthN / AuthZ

## AuthN

- Actor 注入：从请求中解析用户身份（JWT/Session/Dev override 等）。

## AuthZ（Phase 0）

- 隔离边界：Library owner（`library.user_id`）
- 用例入口统一 owner-check：越权返回 403（DomainException -> HTTP）

## 演进

- tenant/workspace 表落地后，把 scope key 从 owner 迁移到 tenant/workspace。
