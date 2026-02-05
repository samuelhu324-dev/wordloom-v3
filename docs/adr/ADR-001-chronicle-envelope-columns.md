# ADR-001: Chronicle envelope 升列（Phase C）

Status: Adopted

## Context
最初 envelope 放在 payload 内用于快速止血，但在产品化阶段：
- 查询需要稳定列（排序/过滤/索引）
- payload 作为 JSONB 不适合作为主要检索接口

## Decision
将以下字段提升为 `chronicle_events` 的列并建立必要索引：
- `schema_version`
- `provenance`
- `source`
- `actor_kind`
- `correlation_id`

迁移策略：
- 先 nullable + backfill（仅对可确定来源字段）
- 新写入双写（列优先）
- `server_default` 只用于“语义无害”的字段；`correlation_id` 不设置默认，避免伪造链路
- 暂缓 NOT NULL（避免历史数据伪精确回填/审计污染）

## Consequences
- ✅ 查询/索引稳定
- ✅ 迁移不被历史数据阻塞
- ⚠️ 需要保持 payload 兼容窗口（逐步迁移读路径）

## Links
- docs/chronicle/STATUS.md#phase-c
- docs/logs/others/others-047-source-of-truth-projection-chronicle-7.md
