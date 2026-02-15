保留 DDD_RULES 这个名字是合理的，因为它记录的是领域建模与不变量/政策；

Hexagonal 没有“官方规则表”命名，更像一套边界/依赖/适配器实践；

做法：不要拆成两个平行规则库（容易漂移），而是一个总规则库，把 Hexagonal 的部分作为独立章节/命名空间合入。

推荐做法（单一事实源）

把 DDD_RULES.yaml 升级为 SYSTEM_RULES.yaml（或继续叫 DDD_RULES.yaml 也行），结构分区：
version: "3.1"
metadata:
  architecture: ["DDD", "Hexagonal"]

ddd:
  invariants:    # 不变量
  policies:      # 业务政策
  aggregates:    # 聚合及边界

hexagonal:
  ports:
    inbound:     # REST/CLI/Job/Test 入口端口
    outbound:    # Repository/EventBus/Storage/Search 等
  adapters:
    rules:       # 适配器约束：不得返回 ORM，不得泄露 SDK 类型…
  di:
    composition_root: # DI 链：Session -> Repo -> Service
  testing:
    pyramid:     # Unit/Contract/Integration/E2E
    fakes:       # InMemory 实现清单
  error_mapping:
    NotFoundError: 404
    ConflictError: 409
    ValidationError: 422
  observability:
    structured_logging: # 必备字段：request_id/user_id/resource/error_code/latency_ms
  performance:
    pagination: { default_limit: 20, max_limit: 100 }

领域（ddd:）记录“业务真相”；六边形（hexagonal:）记录“系统边界与连接规则”。一个文件统管，ADR 负责“为什么”。
