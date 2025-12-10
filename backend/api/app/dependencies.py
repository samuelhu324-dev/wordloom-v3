"""
Dependency Injection Container - Routes to UseCases

完整真实模式（Complete Real Mode Nov 17, 2025）：
- Library: 真实 SQLAlchemy async Repository ✅
- Bookshelf: 真实 SQLAlchemy async Repository ✅
- Book: 真实 SQLAlchemy async Repository ✅
- Block: 真实 SQLAlchemy async Repository + Paperballs recovery ✅

Architecture: Hexagonal Pattern
- Routes (HTTP Adapter) → DI Container → UseCases → Repositories
- Pattern: Factory Method for UseCase instantiation
- All repositories are async and database-backed

CRITICAL FIX (Nov 19, 2025):
- Only import get_db_session (NOT AsyncSessionLocal - lazy loaded)
- Event loop policy set in launcher before any imports
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.session import get_db_session

# Import real container and re-export it as DIContainer for backward compatibility
from api.app.dependencies_real import DIContainerReal as DIContainer
from api.app.dependencies_real import DIContainerReal

__all__ = ["DIContainerReal", "DIContainer", "get_di_container"]


async def get_di_container(session: AsyncSession = Depends(get_db_session)) -> DIContainerReal:
    """
    提供真实 DI 容器给路由层 (Production Mode)

    返回所有真实 async Repository 的 DIContainerReal 实例

    所有 22 个 UseCase 工厂方法都使用真实的 SQLAlchemy async Repository
    - Library: AsyncSession ready
    - Bookshelf: AsyncSession ready
    - Book: AsyncSession ready
    - Block: AsyncSession ready (包括 Paperballs 恢复逻辑)

    数据库持久化：所有操作都直接影响 PostgreSQL
    """
    return DIContainerReal(session)