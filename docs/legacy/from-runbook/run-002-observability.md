# Observability

## Kanban
---

- **id**: S0
- **area**: chronicle-projection
- **status**: active 
- **applies_to**: >=S0 <=S1
- **related**:
 - **issues**: 
 - **adrs**: 
- **last_updated**: 2026-02-12
- **owners**: [samuel]

---

## Prometheus scrape

- 配置：docker/prometheus/prometheus.yml
- 目标：API（dev/test 端口）+ worker（dev/test 端口）

说明：Prometheus 容器通过 host.docker.internal 抓取宿主机（Docker Desktop 场景）。

## Grafana

- provisioned dashboards：docker/grafana/dashboards/
- 当前已有：Wordloom • Outbox + ES Bulk

## Metrics 设计原则

- 默认低基数（labels 控制在 env/component/projection/op/reason）
- library 维度拆分用 bucket 或 Top-N（避免直接 library_id）

## 推荐看板信号

- produced vs processed（速率）
- lag events（队列积压）
- oldest outbox age（投影新鲜度）
- failed rate / 429 ratio（稳定性）
