1. 快速梳理老架构（30 分钟）
   └─ 打开 WordloomBackend 的关键文件
   └─ 记录到 DDD_RULES.yaml 的 legacy_source

2. 确认第一个 Domain（30 分钟）
   └─ Library 是最简单的聚合根
   └─ 明确它的 Rules 和 Policies

3. 制定 Week 1 的具体目标（20 分钟）
   └─ 只实现 5 个 Domain（Library, Bookshelf, Book, Block, Tag）
   └─ 暂不考虑 Hexagonal，专注 DDD 的正确性

目标：既要快速看到成果，也要保证架构质量

策略：
  ├─ Week 1：用"轻量级 Hexagonal"
  │   ├─ 有 domain.py（纯业务逻辑）
  │   ├─ 有 repository.py（但先不用 Port，直接 SQLAlchemy）
  │   └─ 有 service.py（简单的业务协调）
  │
  └─ Week 2：升级为"完整 Hexagonal"
      ├─ 提取 Ports（interfaces）
      ├─ 创建 Adapters（实现）
      └─ 使用 Dependency Injection

调整后的结构（Week 1 - 轻量 Hexagonal）
backend/api/app/modules/library/
├─ __init__.py
├─ domain.py          ← ✅ Pure Domain Logic（无依赖）
├─ models.py          ← ✅ ORM Models（SQLAlchemy）
├─ schemas.py         ← ✅ API DTOs
├─ repository.py      ← ✅ Repository 实现（直接 SQL）
├─ service.py         ← ✅ 业务逻辑协调
├─ router.py          ← ✅ FastAPI endpoints
├─ exceptions.py      ← ✨ 新增（Domain exceptions）
└─ tests/
    ├─ __init__.py
    ├─ test_domain.py         ← 测试 domain.py
    ├─ test_service.py        ← 测试 service.py
    └─ conftest.py            ← ✨ 新增（pytest fixtures）

Week 2 升级后的结构（完整 Hexagonal）
backend/api/app/modules/library/
├─ __init__.py
├─ core/                      ← ✨ 新增目录
│   ├─ __init__.py
│   ├─ domain.py              ← ✅ 从上级搬过来（保持不变）
│   ├─ ports.py               ← ✨ 新增（Repository Port）
│   └─ dto.py                 ← ✨ 新增（内部 DTO）
│
├─ adapters/                  ← ✨ 新增目录
│   ├─ __init__.py
│   ├─ orm_models.py          ← ✅ 从 models.py 搬过来
│   ├─ repository.py          ← ✅ 从上级搬过来，现在实现 Port
│   └─ event_adapter.py       ← ✨ 新增（事件适配器）
│
├─ api/                       ← ✨ 新增目录
│   ├─ __init__.py
│   ├─ schemas.py             ← ✅ 从上级搬过来
│   └─ router.py              ← ✅ 从上级搬过来
│
├─ exceptions.py              ← ✅ 保持
│
└─ tests/
    ├─ __init__.py
    ├─ unit/
    │   ├─ test_domain.py
    │   └─ test_dto.py
    ├─ integration/
    │   ├─ test_repository.py
    │   └─ test_service.py
    ├─ api/
    │   └─ test_router.py
    └─ conftest.py


