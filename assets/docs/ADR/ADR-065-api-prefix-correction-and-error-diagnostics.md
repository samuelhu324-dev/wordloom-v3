# ADR-065: API 前缀回滚至 /api/v1 并改进错误诊断

Date: 2025-11-17
Status: Accepted
Supersedes: ADR-064

## 背景
后端 `backend/api/app/main.py` 通过 `app.include_router(..., prefix='/api/v1/xxx')` 注册所有路由，真实前缀为 `/api/v1`。之前误判为 `/api` 导致前端改写前缀，产生持续 404/500 错误。

## 问题
- 前端与后端前缀不一致：`/api` vs `/api/v1`。
- 错误提示不够清晰，仅显示 500，不展示后端返回体。

## 决策
1. 统一恢复 `/api/v1` 为默认前缀（`API_PROXY_PREFIX`, `NEXT_PUBLIC_API_PREFIX`）。
2. 后续在库列表组件中增加详细错误信息（状态码 + detail）。

## 实施
- 回滚 `client.ts`, `config.ts`, `next.config.js`, `.env.local` 前缀为 `/api/v1`。
- 更新 `VISUAL_RULES.yaml` 标记更正状态。
- 计划下一步：增强库列表错误显示。

## 验收标准
1. 浏览器请求为 `GET /api/v1/libraries`。
2. 若后端正常：200 返回库数组；若空：200 + []；错误时前端显示后端 detail。

## 回滚方案
若未来后端切换 `/api`：同时更新环境变量与上述三处配置，再发布 ADR-066。

## 相关
- ADR-063: Real Data Mode Same-Origin Proxy
- ADR-064:（被更正）
