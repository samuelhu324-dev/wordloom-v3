"""
===============================================================================
HEXAGONAL ARCHITECTURE - STEP 8 DETAILED PLAN
===============================================================================

任务: 完成 Hexagonal 转换的最后一步 - DI 容器 + Router 重构 + 应用启动

总体完成度: 87.5% (7/8) → 目标: 100% (8/8)
预计时间: 1.5-2 小时

===============================================================================
STEP 8 分解任务
===============================================================================

主要任务分为 3 个部分:

1️⃣  **Part A: 创建 DI 容器** (30 分钟)
   Location: backend/api/dependencies.py
   内容:
   └─ DIContainer 类
      ├─ Repository 创建
      ├─ UseCase 创建和注入
      ├─ EventBus 初始化
      └─ 所有依赖的生命周期管理

2️⃣  **Part B: 重构 Routers** (1 小时)
   对所有 6 个模块的 routers 进行改造:

   Tag Router (modules/tag/routers/tag_router.py):
   ├─ 接收 DIContainer 注入
   ├─ 从 DI 容器获取 UseCase 实例
   ├─ 重构所有端点：Request DTO → UseCase → Response DTO
   └─ 共 ~10 个端点需要改造

   Media Router (modules/media/routers/media_router.py):
   ├─ 类似 Tag 模式
   └─ 共 ~10 个端点

   ... (Bookshelf, Book, Block, Library)

3️⃣  **Part C: 应用启动** (30 分钟)
   Location: backend/api/app/main.py
   内容:
   ├─ 初始化 FastAPI 应用
   ├─ 初始化 EventBus
   ├─ 创建 DI 容器
   ├─ 注册所有 Routers
   ├─ 设置事件处理器
   └─ 启动 lifespan handlers

===============================================================================
PART A: DI 容器 (dependencies.py)
===============================================================================

结构:

class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        # 1. 数据库会话工厂
        self.session_factory = SessionLocal

        # 2. 单例 EventBus
        self.event_bus = get_event_bus()

        # 3. Repository 实例（单例或请求作用域）
        self.tag_repository = None      # 延迟初始化
        self.media_repository = None
        self.bookshelf_repository = None
        self.book_repository = None
        self.block_repository = None
        self.library_repository = None

    def get_session(self):
        """获取数据库会话（依赖注入提供者）"""
        return self.session_factory()

    def get_tag_repository(self) -> ITagRepository:
        """获取 Tag Repository"""
        session = self.get_session()
        return SQLAlchemyTagRepository(session)

    # ... 其他 repository 类似

    def get_create_tag_use_case(self) -> CreateTagUseCase:
        """获取 CreateTagUseCase"""
        repo = self.get_tag_repository()
        return CreateTagUseCase(repo, self.event_bus)

    # ... 其他 use case

使用模式:

@app.get("/tags")
def list_tags(
    di: DIContainer = Depends(get_di_container),
    request: SearchTagsRequest = Query(...)
):
    use_case = di.get_search_tags_use_case()
    response = await use_case.execute(request)
    return response.to_dict()

===============================================================================
PART B: Router 重构模式
===============================================================================

重构前（旧模式）:

@router.post("/tags", response_model=TagResponse)
async def create_tag(request: CreateTagRequest):
    service = TagService()  # 直接创建
    result = service.create_tag(...)  # 调用 service
    return result

重构后（新模式）:

@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    di: DIContainer = Depends(get_di_container)  # 注入 DI
):
    use_case: CreateTagUseCase = di.get_create_tag_use_case()
    response: TagResponse = await use_case.execute(request)
    return response.to_dict()

关键改变:
✓ Service → UseCase (更细粒度)
✓ 直接创建 → DI 容器注入
✓ 业务对象 → DTO 模式
✓ EventBus 自动处理

所有 Router 都遵循这个模式!

===============================================================================
PART B 详细步骤 - Tag Router 示例
===============================================================================

endpoints 列表（tag_router.py）:

1. POST /tags
   Request: CreateTagRequest
   UseCase: CreateTagUseCase
   Response: TagResponse

2. POST /tags/{id}/subtags
   Request: CreateSubtagRequest
   UseCase: CreateSubtagUseCase
   Response: TagResponse

3. GET /tags/{id}
   Request: GetTagRequest
   UseCase: 需要新增 GetTagUseCase
   Response: TagResponse

4. PATCH /tags/{id}
   Request: UpdateTagRequest
   UseCase: UpdateTagUseCase
   Response: TagResponse

5. DELETE /tags/{id}
   Request: DeleteTagRequest
   UseCase: DeleteTagUseCase
   Response: None (204)

6. POST /tags/{id}/restore
   Request: RestoreTagRequest
   UseCase: RestoreTagUseCase
   Response: TagResponse

7. GET /tags (search/list)
   Request: SearchTagsRequest
   UseCase: SearchTagsUseCase
   Response: List[TagResponse]

8. GET /tags/most-used
   Request: GetMostUsedTagsRequest
   UseCase: GetMostUsedTagsUseCase
   Response: List[TagResponse]

9. POST /tags/{tag_id}/associate
   Request: AssociateTagRequest
   UseCase: AssociateTagUseCase
   Response: None (200)

10. DELETE /tags/{tag_id}/disassociate
    Request: DisassociateTagRequest
    UseCase: DisassociateTagUseCase
    Response: None (200)

这是 Tag Router 的完整重构。

其他模块（Media, Bookshelf, Book, Block, Library）类似。

===============================================================================
PART C: 应用启动 (main.py)
===============================================================================

from fastapi import FastAPI
from contextlib import asynccontextmanager

from infra.event_bus import get_event_bus, EventBus
from infra.event_handler_registry import setup_event_handlers
from dependencies import DIContainer, get_di_container
from modules.tag.routers import tag_router
from modules.media.routers import media_router
# ... 其他 routers

# 全局 DI 容器
di_container: DIContainer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期处理"""
    # 启动事件
    print("🚀 Starting Wordloom API...")

    # 初始化 EventBus
    event_bus = get_event_bus()

    # 初始化 DI 容器
    global di_container
    di_container = DIContainer(event_bus)

    # 设置事件处理器
    setup_event_handlers(event_bus)

    print(f"✅ EventBus initialized with {len(event_bus.get_handlers(None))} handlers")
    print("✅ DI container ready")

    yield

    # 关闭事件
    print("🛑 Shutting down Wordloom API...")

# 创建 FastAPI 应用
app = FastAPI(
    title="Wordloom API",
    description="Book Management System with Hexagonal Architecture",
    version="1.0.0",
    lifespan=lifespan
)

# 注册所有 Routers
app.include_router(tag_router.router, prefix="/api/tags", tags=["Tags"])
app.include_router(media_router.router, prefix="/api/media", tags=["Media"])
app.include_router(bookshelf_router.router, prefix="/api/bookshelves", tags=["Bookshelves"])
app.include_router(book_router.router, prefix="/api/books", tags=["Books"])
app.include_router(block_router.router, prefix="/api/blocks", tags=["Blocks"])
app.include_router(library_router.router, prefix="/api/libraries", tags=["Libraries"])

# 依赖注入提供者
def get_di_container_provider() -> DIContainer:
    global di_container
    if di_container is None:
        di_container = DIContainer(get_event_bus())
    return di_container

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# 启动函数
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

===============================================================================
执行计划时间表
===============================================================================

⏱️  Part A: DI 容器 (30 分钟)
   ├─ 15 分钟: 创建 dependencies.py 框架
   ├─ 10 分钟: 实现 6 个 Repository 工厂方法
   └─ 5 分钟: 实现所有 UseCase 工厂方法

⏱️  Part B: Router 重构 (60 分钟)
   ├─ 15 分钟: Tag Router (10 个端点)
   ├─ 10 分钟: Media Router (9 个端点)
   ├─ 10 分钟: Bookshelf Router (6 个端点)
   ├─ 10 分钟: Book Router (7 个端点)
   ├─ 10 分钟: Block Router (8 个端点)
   └─ 5 分钟: Library Router (2 个端点)

⏱️  Part C: 应用启动 (30 分钟)
   ├─ 10 分钟: 创建 main.py
   ├─ 10 分钟: 集成 EventBus 和 DI 容器
   └─ 10 分钟: 测试和调试

总计: 120 分钟 (2 小时)

===============================================================================
成功标志 (成功完成标准)
===============================================================================

✅ Part A 完成:
   - DIContainer 类完整实现
   - 所有 6 个 Repository 工厂方法
   - 所有 41 个 UseCase 工厂方法
   - 依赖注入提供者函数

✅ Part B 完成:
   - 所有 6 个模块的 Router 重构完成
   - 所有端点使用 DTO 模式
   - 所有 UseCase 从 DI 容器获取
   - 端点总数: 10 + 9 + 6 + 7 + 8 + 2 = 42 个端点

✅ Part C 完成:
   - main.py 完整实现
   - 应用启动时初始化 EventBus
   - 应用启动时创建 DI 容器
   - 应用启动时设置事件处理器
   - 应用可以成功启动

✅ 整体:
   - 所有 8 个 Step 完成 (100%)
   - Hexagonal 架构完全转换完毕
   - 事件驱动、依赖注入、DTO 模式全面应用
   - 代码完全解耦，易于测试和扩展

===============================================================================
关键文件列表 (Step 8 涉及)
===============================================================================

需要创建/更新的文件:

1. backend/api/dependencies.py (新建) - DI 容器
2. backend/api/app/main.py (更新) - 应用启动
3. modules/tag/routers/tag_router.py (更新) - Router 重构
4. modules/media/routers/media_router.py (更新) - Router 重构
5. modules/bookshelf/routers/bookshelf_router.py (更新) - Router 重构
6. modules/book/routers/book_router.py (更新) - Router 重构
7. modules/block/routers/block_router.py (更新) - Router 重构
8. modules/library/routers/library_router.py (更新) - Router 重构

可选增强:
9. backend/api/app/docs/__init__.py - API 文档
10. backend/api/app/tests/test_di_container.py - DI 容器测试
11. backend/api/app/tests/test_routers.py - Router 集成测试

===============================================================================
预期结果
===============================================================================

🎉 完成 Step 8 后:

📊 架构完整度: 100%
   ✓ Domain Layer: 完成
   ✓ Application Layer (UseCase): 完成
   ✓ Ports (Input/Output): 完成
   ✓ Infrastructure (EventBus): 完成
   ✓ Adapters (Routers + DI): 完成

🔧 技术栈就绪:
   ✓ Hexagonal 架构
   ✓ 事件驱动
   ✓ 依赖注入
   ✓ DTO 模式
   ✓ 异步处理
   ✓ 错误处理

📈 代码质量:
   ✓ 完全解耦
   ✓ 易于测试
   ✓ 易于扩展
   ✓ 可维护性高
   ✓ 业务逻辑清晰

🚀 准备生产:
   ✓ 应用可启动
   ✓ 所有端点可用
   ✓ EventBus 可用
   ✓ 错误处理完善
   ✓ 日志记录完善

===============================================================================
"""
