# ADR-064: API 前缀统一为 /api 并启用真实数据库

Date: 2025-11-17
Status: Accepted
Type: Frontend/Backend Integration Fix

## 背景
此前前端默认使用 `/api/v1`，后端路由实际注册为 `/api/...` (如 `/api/libraries`)。请求 `/api/v1/libraries` 被代理到后端不存在的路径，出现 404/500，页面显示“加载库失败”。

## 问题
1. 前缀不一致：前端硬编码 `/api/v1`，后端使用 `/api`。
2. 多处重复定义：`next.config.js`、`client.ts`、`config.ts` 各自写死，易偏差。
3. 错误表现：DevTools 中多次 500/404，库列表加载失败。

## 决策
统一使用 `/api` 作为本地与后端一致的前缀。通过 `API_PROXY_PREFIX` 与 `NEXT_PUBLIC_API_PREFIX` 环境变量控制，默认值 `/api`。保留可配置能力，如后端未来引入版本化再切换。

## 具体改动
- `frontend/.env.local`：`API_PROXY_PREFIX=/api`，新增 `NEXT_PUBLIC_API_PREFIX=/api`。
- `frontend/next.config.js`：默认前缀改为 `/api`。
- `frontend/src/shared/api/client.ts` & `config.ts`：读取环境变量，不再硬编码 `/api/v1`。
- `VISUAL_RULES.yaml`：更新 `api_prefix` 与连接状态描述。

## 效果
- 请求基准 `http://localhost:30001/api/...` 与后端真实路由匹配，库列表请求 `GET /api/libraries` 应返回 2xx。
- Mock 已禁用 (`NEXT_PUBLIC_USE_MOCK=0`)，真实数据库成为唯一来源。

## 验收标准
1. 访问 `/admin/libraries` 时网络请求为 `GET /api/libraries` 返回 200/204（空）或 200（含数据）。
2. 控制台不再出现针对 `/api/v1/libraries` 的 404/500。
3. VISUAL_RULES.yaml 中的前缀与状态与实际运行一致。

## 回滚方案
若需恢复旧版本前缀：设置 `API_PROXY_PREFIX=/api/v1` 与 `NEXT_PUBLIC_API_PREFIX=/api/v1` 并重启前端；必要时重新启用 mock：`NEXT_PUBLIC_USE_MOCK=1`。

## 后续
- 收敛前缀定义来源（长期只保留环境 + 单一 config）。
- 编写端到端测试覆盖“库列表加载成功/空状态”。
- 若未来引入版本化，可采用 `/api/v2` 后台 alias + 前端灰度切换。

## 相关
- ADR-063: Real Data Mode Same-Origin Proxy
- VISUAL_RULES.yaml (更新于 2025-11-17)
