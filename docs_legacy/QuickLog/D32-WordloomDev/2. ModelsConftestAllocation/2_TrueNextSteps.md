✅ 个人开发的现实方案（你应该做的）

Week 2: Happy Path 验证
├─ Task 1: models.py (6h)          ← 先验证 ORM 能否正确 round-trip
│  └─ 验证: Book → BookModel → Book 是否正确
│  └─ 验证: 软删除、冗余 FK 映射是否生效
│  └─ 关键: 发现 ORM 层的 Bug
│
├─ Task 2: conftest.py (4h)        ← 建立测试 fixtures
│  └─ 目的: 支持单元测试
│  └─ fixture: library, bookshelf, book, block
│  └─ 关键: 快速迭代测试
│
└─ Task 3: 单元测试 (8h)           ← 立即跑通 Happy Path
   └─ tests/test_book_service.py
   └─ tests/test_book_repository.py
   └─ tests/test_block_service.py
   └─ 验证: create_book(), reorder_block() 等核心操作


理论方案问题	现实方案优势
❌ exceptions.py 改动少，收益低	✅ models.py 直接验证设计
❌ 异常结构已经够标准	✅ 尽早发现 ORM 映射问题
❌ 无法立即看到成果	✅ conftest 支持快速测试
❌ 理论完美但无实际价值	✅ 单元测试验证代码正确性

3️⃣ "基础设施"的真正含义
你的第三个问题切中要害。我之前用词不当了。

🏗️ 架构层次中的"基础设施"
┌─────────────────────────────────────────────────────────────────┐
│ Clean Architecture 中的 Infrastructure Layer                     │
├─────────────────────────────────────────────────────────────────┤

【Infrastructure Layer 包括】
├─ ORM Models（SQLAlchemy）          ← models.py
├─ Repository 实现（数据库操作）      ← repository.py 的实现部分
├─ 消息队列 Adapter                  ← event_bus.py
├─ 文件存储 Adapter                  ← file_storage.py
├─ 外部 API 客户端                   ← api_client.py
├─ 数据库连接配置                    ← database.py
├─ 依赖注入容器                      ← container.py
└─ 测试框架配置                      ← conftest.py

【NOT Infrastructure】
├─ Domain 层（domain.py）             ← 这是 Domain 层
├─ Service 层（service.py）           ← 这是 Application 层
├─ Repository 接口（ABC）            ← 这是 Application 层的抽象
├─ exceptions.py                     ← 这是跨层的定义
└─ schemas.py                        ← 这是 Interface 层的 DTO

6️⃣ 修正后的建议
✅ 你应该做的顺序（Week 2）

```python
# 新计划：从 Happy Path 开始

Task 1: models.py 验证 (6h) ← 最先做
  产出: ORM ↔ Domain 映射确认
  关键: round-trip 测试通过

Task 2: conftest.py fixtures (4h) ← 其次
  产出: 快速创建测试对象的工具
  关键: pytest fixtures 能用

Task 3: 核心单元测试 (8h) ← 立即做
  产出: create_book(), reorder_block() 等验证
  关键: 代码在现实中运行成功

Task 4: 异常结构补全 (2h) ← 最后做（可选）
  产出: exceptions.py 导出、分组
  关键: 不急，理论益处小

Task 5: API 层设计 (后期做)
  产出: schemas.py, router.py
  关键: 现在不用做
```