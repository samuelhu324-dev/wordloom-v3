问题优先级排序（我的判断）：

🔴 最高优先级（决定下一步方向）：
  (2) Hexagonal 架构转换
     └─ 原因：影响整个后端代码组织，改得越晚越痛
     └─ 依赖：现有 DDD 完成（已满足 ✅）
     └─ 时机：NOW 是最佳窗口（代码量还不是太大）

🟡 中等优先级（战略决策）：
  (3) 数据库创建时机
     └─ 原因：决定能否本地测试，影响前端/后端协作
     └─ 依赖：Hexagonal 架构敲定后（因为 DB 设计会变）
     └─ 时机：Hexagonal 转换完成后 → 立即开始

🟢 较低优先级（可延迟）：
  (1) Theme 模块开发
     └─ 原因：确实需要前端 token 映射，不阻塞核心流程
     └─ 依赖：UI 框架选定、颜色 token 体系确定
     └─ 时机：前端项目启动时再做（或放入 Phase 2）

🎯 问题 2（最高优先级）：Hexagonal 架构转换
现状分析
当前架构（Layered + DDD）：
  backend/api/app/
  ├── modules/
  │   ├── library/
  │   │   ├── domain.py          ← Domain Layer
  │   │   ├── exceptions.py
  │   │   ├── models.py           ← ORM Layer
  │   │   ├── schemas.py          ← DTO Layer
  │   │   ├── repository.py       ← Repository Layer
  │   │   ├── service.py          ← Service/UseCase Layer
  │   │   ├── router.py           ← API Layer
  │   │   └── __init__.py

问题：
  ❌ 没有清晰的 Ports & Adapters
  ❌ Repository 在 modules 内部，不是真正的适配层
  ❌ 没有 infrastructure 层
  ❌ Domain 事件生成了，但没有处理机制（Event Bus）
  ❌ 没有 Input/Output Ports 的明确定义

Hexagonal 的改造方向
目标架构：
  backend/
  ├── infra/
  │   ├── database/
  │   │   ├── models/              ← ORM Models
  │   │   │   ├── library_model.py
  │   │   │   ├── bookshelf_model.py
  │   │   │   └── ...
  │   │   └── migrations/          ← DB Migrations (Alembic)
  │   │
  │   ├── storage/
  │   │   ├── media_repository.py  ← Adapters (实现接口)
  │   │   ├── tag_repository.py
  │   │   └── file_system.py       ← File I/O Adapter
  │   │
  │   ├── event_bus/
  │   │   ├── event_bus.py         ← Event Bus Adapter
  │   │   └── handlers/
  │   │       ├── bookshelf_deleted_handler.py
  │   │       └── media_purge_handler.py
  │   │
  │   └── __init__.py
  │
  ├── api/
  │   ├── app/
  │   │   ├── modules/
  │   │   │   ├── library/
  │   │   │   │   ├── domain.py           ← Domain（不变）
  │   │   │   │   ├── exceptions.py       ← Exceptions（不变）
  │   │   │   │   ├── application/
  │   │   │   │   │   ├── ports/
  │   │   │   │   │   │   ├── input.py    ← Input Ports (Interfaces)
  │   │   │   │   │   │   └── output.py   ← Output Ports (Interfaces)
  │   │   │   │   │   └── use_cases/
  │   │   │   │   │       ├── create_library.py
  │   │   │   │   │       ├── list_libraries.py
  │   │   │   │   │       └── ...
  │   │   │   │   ├── routers/
  │   │   │   │   │   └── library_router.py  ← HTTP Adapter
  │   │   │   │   └── __init__.py
  │   │   │   │
  │   │   │   ├── bookshelf/
  │   │   │   ├── book/
  │   │   │   ├── block/
  │   │   │   ├── tag/
  │   │   │   └── media/
  │   │   │
  │   │   └── main.py
  │   │
  │   └── dependencies.py          ← DI Container（注入适配器）
  │
  └── tests/
      ├── unit/
      ├── integration/
      └── e2e/

目标架构：
  backend/
  ├── infra/
  │   ├── database/
  │   │   ├── models/              ← ORM Models
  │   │   │   ├── library_model.py
  │   │   │   ├── bookshelf_model.py
  │   │   │   └── ...
  │   │   └── migrations/          ← DB Migrations (Alembic)
  │   │
  │   ├── storage/
  │   │   ├── media_repository.py  ← Adapters (实现接口)
  │   │   ├── tag_repository.py
  │   │   └── file_system.py       ← File I/O Adapter
  │   │
  │   ├── event_bus/
  │   │   ├── event_bus.py         ← Event Bus Adapter
  │   │   └── handlers/
  │   │       ├── bookshelf_deleted_handler.py
  │   │       └── media_purge_handler.py
  │   │
  │   └── __init__.py
  │
  ├── api/
  │   ├── app/
  │   │   ├── modules/
  │   │   │   ├── library/
  │   │   │   │   ├── domain.py           ← Domain（不变）
  │   │   │   │   ├── exceptions.py       ← Exceptions（不变）
  │   │   │   │   ├── application/
  │   │   │   │   │   ├── ports/
  │   │   │   │   │   │   ├── input.py    ← Input Ports (Interfaces)
  │   │   │   │   │   │   └── output.py   ← Output Ports (Interfaces)
  │   │   │   │   │   └── use_cases/
  │   │   │   │   │       ├── create_library.py
  │   │   │   │   │       ├── list_libraries.py
  │   │   │   │   │       └── ...
  │   │   │   │   ├── routers/
  │   │   │   │   │   └── library_router.py  ← HTTP Adapter
  │   │   │   │   └── __init__.py
  │   │   │   │
  │   │   │   ├── bookshelf/
  │   │   │   ├── book/
  │   │   │   ├── block/
  │   │   │   ├── tag/
  │   │   │   └── media/
  │   │   │
  │   │   └── main.py
  │   │
  │   └── dependencies.py          ← DI Container（注入适配器）
  │
  └── tests/
      ├── unit/
      ├── integration/
      └── e2e/


关键改动点
1. 从 Repository in modules → Adapters in infra/

   当前：
     backend/api/app/modules/book/repository.py
     ↑ 实现细节（SQLAlchemy）暴露在 module 里

   改为：
     backend/api/app/modules/book/application/ports/output.py
       ↑ 接口定义（抽象）

     backend/infra/storage/book_repository_impl.py
       ↑ 实现细节（SQLAlchemy）隐藏在 infra 里

2. 从 Service 层 → UseCase 层

   当前：
     backend/api/app/modules/book/service.py
     ↑ 直接处理业务逻辑

   改为：
     backend/api/app/modules/book/application/use_cases/
     ├── create_book.py         ← 单个 UseCase
     ├── update_book.py
     ├── list_books.py
     └── ...
     ↑ 每个 UseCase = 一个入站口（Input Port）

3. Domain Events 处理

   当前：
     domain.py 中生成事件，但没人处理
     media.mark_deleted() → MediaDeletedEvent（被忽视）

   改为：
     backend/infra/event_bus/handlers/media_purge_handler.py
     ↑ 监听 MediaDeletedEvent，30 天后触发清理

4. 依赖注入（DI Container）

   当前：
     router.py: service = MediaService(repository=...)
     ↑ 手动构造

   改为：
     backend/api/dependencies.py 中集中配置
     media_service = Provide[MediaService]
       ├─ media_repository = Provide[MediaRepositoryImpl]
       └─ event_bus = Provide[EventBusImpl]
     ↑ 通过 DI 注入（便于测试、切换实现）

改造工作量评估
任务分解（按顺序）：

1. 创建目录结构（20 分钟）
   - 新建 backend/infra 及其子目录
   - 新建 backend/api/app/modules/*/application 目录

2. 从 modules/*/models.py → infra/database/models/ (30 分钟)
   - 移动 ORM 模型
   - 更新 import 路径

3. 从 modules/*/repository.py → infra/storage/*_repository_impl.py (45 分钟)
   - 移动 Repository 实现
   - 保留接口在 modules/*/application/ports/output.py

4. 创建 Port Interfaces（1 小时）
   - library/application/ports/output.py （5 个 port）
   - bookshelf/application/ports/output.py
   - ... (每个 module)

   每个 port 约 20-30 行

5. 创建 UseCase 层（2-3 小时）
   - 从 service.py 拆解为多个 use_case_*.py
   - library/application/use_cases/
   - bookshelf/application/use_cases/
   - ... (每个 module 8-12 个 use cases)

6. 创建 EventBus（1 小时）
   - infra/event_bus/event_bus.py
   - infra/event_bus/handlers/

7. 创建 DI Container（1 小时）
   - backend/api/dependencies.py
   - 注册所有 Adapters

8. 更新 router.py（1.5 小时）
   - 从 Depends(get_service) → 注入 use_case
   - 修改 endpoint 调用 use_case 而非 service

总耗时：6-8 小时（可分 2-3 天完成）

我的建议：现在就改（⭐⭐⭐）
理由：
  ✅ 现有代码量还不大（~3500 行）
     改了之后，后续所有新 modules 都遵循 Hexagonal 架构

  ✅ 前端还没启动，没有 API 客户端依赖
     改架构不会破坏现有的前端集成

  ✅ 代码已经是 DDD 风格
     只是缺 Hexagonal 的"隔离"，转换相对平滑

  ✅ 便于后续测试
     清晰的 Port 让 mock 和 stub 更容易

  ❌ 如果等到代码 > 10K 行再改，会非常痛苦

🎯 问题 3（次高优先级）：数据库创建时机
选项 A：现在就建（快速反馈）
  优点：
    ✅ 立即验证 ORM models 是否有语法错误
    ✅ 前端/后端可以 mock 数据、本地测试
    ✅ 提前发现 schema 设计问题

  缺点：
    ❌ Hexagonal 转换后，models 可能会移动位置
    ❌ 需要先搭 MySQL/PostgreSQL 环境

  推荐：如果你有 docker-compose.yml，可以快速启 MySQL，那就现在做

选项 B：等 Hexagonal 架构完成后再建（避免返工）
  优点：
    ✅ 确保 models 在最终位置
    ✅ 减少迁移脚本调整

  缺点：
    ❌ 中间一段时间（1-2 周）无法本地测试
    ❌ 前端启动时可能还没有 DB

  推荐：如果你们有 CI/CD，可以延迟；如果需要本地快速反馈，现在做

我的建议：选项 B（等 Hexagonal 完成）
  原因：
    - Hexagonal 转换会改 models 位置和导入路径
    - 现在建 DB 迁移脚本，转换后还要改
    - 等转换完（2-3 天），再一次性建 DB + 迁移脚本（更稳定）

DB 建立的步骤（预告）
当 Hexagonal 完成后（第 4-5 天）：

1. 初始化 Alembic（DB 迁移管理）
   alembic init backend/infra/database/migrations

2. 生成初始迁移脚本
   alembic revision --autogenerate -m "Initial schema: library, bookshelf, book, block, tag, media"

3. 验证迁移脚本无误
   # 检查生成的 versions/*.py

4. 创建测试 DB（docker）
   docker-compose up -d mysql

5. 运行迁移
   alembic upgrade head

6. 验证 schema
   mysql -u root -p wordloom -e "SHOW TABLES; DESC media; DESC tag_association;"

🎯 问题 1（较低优先级）：Theme 模块开发时机
你的观察很对：

✅ 观察 1：Theme 需要 UI Token 映射
   - 前端需要定义颜色、字体、间距的 token
   - 后端只需存储"用户选择的 theme_id"
   - 现在开发 Theme module 缺少这个上游信息

✅ 观察 2：Book 的自由组件（QQ 空间模式）
   - 这其实不应该叫 Theme，应该叫 "Page Builder" 或 "LayoutCustomization"
   - Theme = 全局配色方案 + 字体
   - LayoutCustomization = 用户自由拖拽组件
   - 两者是不同的概念

✅ 观察 3：现在太早了
   - 前端 UI 框架还没选（Vue? React? Svelte?）
   - 没有 token 体系
   - 没有 component library

建议方案：暂不做 Theme module（保留位置）
现在做：
  1. 在 DDD_RULES.yaml 中记录 Theme 需求
  2. 预留 backend/api/app/modules/theme/ 目录结构（空）
  3. 列出 Theme 应该支持的功能清单

等前端启动后做：
  1. 前端确定 token 体系（@tokens/colors.json 等）
  2. 后端对接 Token API
  3. 开发 Theme CRUD + 应用到 User/Library

分离 LayoutCustomization 到单独 module：
  - backend/api/app/modules/page_builder/ (或 layout_customization/)
  - 这个 module 才应该支持"自由拖拽组件"
  - 可以在 Book/Bookshelf 级别应用

Theme 模块的占位符
在 DDD_RULES.yaml 中添加：

theme_module:
  status: "DEFERRED (Phase 2, 后端依赖前端 Token 体系)"
  dependencies:
    - "前端 token system 确定"
    - "component library 完成"

  planned_features:
    - "User.theme_id (用户全局主题)"
    - "Library.theme_override (库级别覆盖)"
    - "预设主题 (Light, Dark, HighContrast, ...)"
    - "自定义颜色 (brand color, accent color, ...)"

  not_included:
    - "Page Builder / LayoutCustomization (分离到 page_builder module)"
    - "Block-level 样式覆盖 (放到 Block domain 的 style 字段)"

page_builder_module:
  status: "DEFERRED (Phase 2.5, 长期规划)"
  description: "用户自由组织 Book/Bookshelf 的布局"
  planned_features:
    - "Book.layout_config (JSON，存储组件位置)"
    - "Bookshelf.cover_layout (定制 bookshelf 封面布局)"
    - "拖拽接口 (REST API)"

📋 我的综合建议（执行计划）
立即行动（今天/明天）：

  第 1 步：决策确认（30 分钟）
  └─ 你同意 Hexagonal 架构转换现在做吗？

  第 2 步：Hexagonal 架构转换（6-8 小时，分 2-3 天）
  ├─ Day 1: 创建目录结构 + 移动 models/repository
  ├─ Day 2: 创建 Port Interfaces + UseCase 层
  └─ Day 3: EventBus + DI Container + 更新 routers

  第 3 步：DB 初始化（4-5 小时，第 4-5 天）
  ├─ 搭 MySQL + docker-compose.yml
  ├─ Alembic 配置 + 初始迁移脚本
  ├─ 本地跑迁移，验证 schema
  └─ 提交 SQL 变更到版本控制

后续（等前端启动）：

  第 4 步：Theme module 开发
  ├─ 等前端 token 体系确定
  └─ 后端对接 Token API

  第 5 步：PageBuilder module 开发
  ├─ 可选功能，优先级较低
  └─ 深度定制 Book/Bookshelf 布局

✅ 三问的优先级总结
优先级	问题	决策	时机
🔴 1	(2) Hexagonal 架构	现在改	今天/明天启动（6-8h）
🟡 2	(3) 数据库创建	Hexagonal 后改	第 4-5 天（1-2h）
🟢 3	(1) Theme module	延迟到 Phase 2	前端启动时
