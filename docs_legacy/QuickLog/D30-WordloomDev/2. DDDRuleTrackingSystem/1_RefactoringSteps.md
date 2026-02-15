从哪里开始：后端优先，从 Domain 层开始
理由：

1. DDD 强调 Domain Model 是核心
2. 前端依赖后端 API 契约
3. Domain 定义好了，前端才知道数据结构

第一阶段：Domain 层（纯业务逻辑，无依赖）
├─ backend/api/app/modules/library/domain.py     ← 定义 Library 聚合根
├─ backend/api/app/modules/bookshelf/domain.py   ← 定义 Bookshelf
├─ backend/api/app/modules/book/domain.py        ← 定义 Book
└─ backend/api/app/modules/block/domain.py       ← 定义 Block 值对象

第二阶段：Repository 接口（定义数据访问契约）
├─ backend/api/app/modules/library/repository.py
├─ backend/api/app/modules/bookshelf/repository.py
├─ backend/api/app/modules/book/repository.py
└─ backend/api/app/modules/block/repository.py

第三阶段：Service 层（业务用例）
├─ backend/api/app/modules/library/service.py
├─ ...

第四阶段：Router 层（API 端点）
├─ backend/api/app/modules/library/router.py
├─ ...

第五阶段：ORM 模型（具体实现细节）
├─ backend/api/app/modules/library/models.py
└─ ...

落地方案
第一天：规则系统
├─ 创建 backend/docs/DDD_RULES.yaml
├─ 创建 .devlog/DEVLOG.md 和 .devlog/RULES_INDEX.md
└─ Git 初次 commit：":docs: 建立 DDD 规则追踪系统"

第二天：项目配置
├─ 创建 backend/pyproject.toml（FastAPI + SQLAlchemy）
├─ 创建 frontend/package.json（Next.js + React Query）
└─ Git commit：":build: 初始化后端和前端配置"

第三天：Domain 层骨架
├─ 创建 backend/api/app/shared/ 文件内容
├─ 创建 backend/api/app/modules/library/domain.py
├─ 创建对应测试文件
└─ Git commit + 在 Wordloom 日记中添加对应条目

第四天：Repository 接口
├─ 定义数据访问契约
└─ 建立测试框架

...以此类推