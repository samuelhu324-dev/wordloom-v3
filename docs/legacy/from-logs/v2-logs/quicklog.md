### - 2026/02/01 - 2026/02/
1. worker -> daemon
  - metrics (bulk + 监控面板系统 + backoff-jitter)
  - 锁 + lease +SKIP LOCKED (claim - processing - ack)
  - retry(attempts - max attempts) / 
  - backoff jitter 
  - fail - DLQ

2. auth + multitenants
  - 隔离边界 + 请求身份 Actor + 统一授权入口 + 强制数据过滤
  - 
  - 
  -     

3. SoT(权限/隔离/约束/事务) + Projection
  - strong / eventual / SLA
  - feature flag
  - boundary card (Search Projection)
  - merge table (outbox)

4. observability
  - metrics (prom+graf)
  - structured logs
  - tracing 

5. docs
  - failure management (labs + runbook)
  - 

6. boot
  - Docker (启动-环境-依赖-一体化)
  - Procfile - honcho
  - 

7. chronicle (user-oriented logs)
  - payload control - table for critical semantics
  - TTL/partition/archive
  - event merging