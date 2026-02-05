# ADR-003: visit logs（book_viewed/book_opened）TTL/抽稀策略

Status: Draft

## Context
`book_viewed` / `book_opened` 等 visit logs 通常是：高频 + 低审计价值。
如果与核心事实事件同表长期保留，会导致：
- 表/索引膨胀
- 写入压力上升
- Timeline 噪声增加

## Decision（提案）
1) 产品层：visit logs 默认不出现在主 Timeline，仅在 “Show visit logs” 下展示。
2) 写入层：对 visit logs 引入 DB 级窗口抽稀（多实例一致），窗口建议 10s~60s 可配。
3) 存储层：对 visit logs 设置 TTL（prune job），在线库只保留最近 N 天（例如 7/30 天）。
4) 冷存储（可选）：需要追溯时再从归档（S3/对象存储）拉取。

## Exit criteria
- visit logs 存量不再无限增长（有可验证的上限策略）
- 排障仍保留最小证据（actor/correlation/http.route）

## Links
- docs/chronicle/STATUS.md#v4
- docs/logs/others/others-047-source-of-truth-projection-chronicle-7.md
