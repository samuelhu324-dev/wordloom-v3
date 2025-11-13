"""
Wordloom API - Main Application Entry Point

初始化 FastAPI 应用，配置所有依赖、Routers 和中间件。

架构:
- Hexagonal Architecture
- Domain-Driven Design
- Event-Driven System
- Dependency Injection
- Async/Await throughout
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker
import logging

# Infrastructure
from app.infra.event_bus import get_event_bus, EventBus
from app.infra.event_handler_registry import setup_event_handlers
from dependencies import DIContainer, get_di_container_provider

# Module Routers
from app.modules.tag.routers.tag_router import router as tag_router
from app.modules.media.routers.media_router import router as media_router
from app.modules.bookshelf.routers.bookshelf_router import router as bookshelf_router
from app.modules.book.routers.book_router import router as book_router
from app.modules.block.routers.block_router import router as block_router
from app.modules.library.routers.library_router import router as library_router


logger = logging.getLogger(__name__)

# ============================================================================
# Global State
# ============================================================================

_event_bus: EventBus | None = None
_di_container: DIContainer | None = None
_session_factory: sessionmaker | None = None


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时:
    1. 初始化数据库会话
    2. 初始化 EventBus
    3. 创建 DI 容器
    4. 注册事件处理器

    关闭时:
    - 清理资源
    """
    global _event_bus, _di_container, _session_factory

    # ===== 启动事件 =====
    print("\n" + "="*60)
    print("🚀 启动 Wordloom API...")
    print("="*60)

    try:
        # 1. 初始化数据库（可选）
        print("📦 初始化数据库会话工厂...")
        # 这里应该从 infra 模块导入 SessionLocal
        # from app.infra.database import SessionLocal
        # _session_factory = SessionLocal

        # 2. 初始化 EventBus
        print("🔌 初始化 EventBus...")
        _event_bus = get_event_bus()

        # 3. 创建 DI 容器
        print("📋 创建 DI 容器...")
        _di_container = DIContainer(_session_factory)

        # 4. 注册事件处理器
        print("📡 注册事件处理器...")
        setup_event_handlers(_event_bus)

        # 输出初始化统计
        handler_count = sum(
            len(handlers)
            for handlers in _event_bus._handlers.values()
        )
        print(f"\n✅ Wordloom API 已启动")
        print(f"   • EventBus: {len(_event_bus._handlers)} 个事件类型")
        print(f"   • 处理器总数: {handler_count} 个")
        print(f"   • DI 容器: 就绪")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        raise

    yield

    # ===== 关闭事件 =====
    print("\n" + "="*60)
    print("🛑 关闭 Wordloom API...")
    print("="*60)

    try:
        # 清理 EventBus
        if _event_bus:
            _event_bus.clear()

        print("✅ 清理完成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n⚠️  关闭异常: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Wordloom API",
    description="Book Management System with Hexagonal Architecture & Event-Driven Design",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 配置允许的来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Register Routers
# ============================================================================

app.include_router(
    tag_router,
    prefix="/api/tags",
    tags=["Tags"],
)

app.include_router(
    media_router,
    prefix="/api/media",
    tags=["Media"],
)

app.include_router(
    bookshelf_router,
    prefix="/api/bookshelves",
    tags=["Bookshelves"],
)

app.include_router(
    book_router,
    prefix="/api/books",
    tags=["Books"],
)

app.include_router(
    block_router,
    prefix="/api/blocks",
    tags=["Blocks"],
)

app.include_router(
    library_router,
    prefix="/api/libraries",
    tags=["Libraries"],
)


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
async def health_check():
    """
    健康检查端点

    返回:
    - status: API 状态
    - version: API 版本
    - event_bus_ready: EventBus 是否就绪
    """
    global _event_bus, _di_container

    return {
        "status": "healthy",
        "version": "1.0.0",
        "event_bus_ready": _event_bus is not None,
        "di_container_ready": _di_container is not None,
    }


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API root",
)
async def root():
    """API 根端点"""
    return {
        "message": "Welcome to Wordloom API",
        "docs": "/docs",
        "version": "1.0.0",
    }


# ============================================================================
# Exception Handlers
# ============================================================================

from fastapi import Request
from fastapi.responses import JSONResponse


# NOTE: 领域异常处理可以稍后添加
# 当确认异常模块正确导入后再启用


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理一般异常"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup():
    """应用启动时的回调"""
    logger.info("Wordloom API startup")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭时的回调"""
    logger.info("Wordloom API shutdown")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
