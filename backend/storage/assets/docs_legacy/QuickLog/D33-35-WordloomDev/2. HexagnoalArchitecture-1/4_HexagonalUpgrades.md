📋 问题诊断

你的观察 100% 准确：

❌ 现状问题：
1. domain/ 既是文件夹又是 .py 文件（冲突）
2. router/ 既是文件夹又是 .py 文件（冲突）
3. application/ 内部不完整
4. infra/ 和 shared/ 和 core/ 结构混乱
5. 没有清晰的"什么该放哪儿"的规则

✅ 成熟架构标准（Hexagonal 最佳实践）
基于 Clean Code + DDD + Hexagonal，一个 module 应该长这样：

backend/api/app/modules/library/
├── __init__.py                           # 模块公开接口
│
├── domain/                               # ❌ 不要是文件！要是文件夹
│   ├── __init__.py
│   ├── library.py                        # AggregateRoot
│   ├── library_name.py                   # ValueObject
│   └── events.py                         # DomainEvents
│
├── application/                          # UseCase 层（新增/必须）
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── input.py                      # Input Port interfaces (UseCase contracts)
│   │   └── output.py                     # Output Port interfaces (Repository contract)
│   │
│   └── use_cases/
│       ├── __init__.py
│       ├── create_library.py             # CreateLibraryUseCase
│       ├── get_library.py                # GetLibraryUseCase
│       ├── delete_library.py             # DeleteLibraryUseCase
│       └── rename_library.py             # RenameLibraryUseCase
│
├── routers/                              # ❌ 不要是单个 .py 文件！要是文件夹
│   ├── __init__.py
│   └── library_router.py                 # HTTP 适配器（FastAPI 路由）
│
├── schemas.py                            # Pydantic DTO (Request/Response)
├── exceptions.py                         # Domain 异常类
└── __init__.py

🎯 阶段 1：仅调整 library 模块（做完再动别的）
步骤 1.1：解决 domain.py 冲突

# ❌ 错误：同时存在
backend/api/app/modules/library/domain.py       # 文件
backend/api/app/modules/library/domain/         # 文件夹

# ✅ 正确：
# 删除文件 domain.py，创建文件夹 domain/

cd backend/api/app/modules/library

# 1. 备份原 domain.py
cp domain.py domain.py.backup

# 2. 创建新 domain/ 目录
mkdir -p domain

# 3. 移动 domain.py 的内容到新文件
# 把 domain.py 的代码剪切到 domain/library.py
# 把 ValueObject 代码剪切到 domain/library_name.py
# 把 events.py 移到 domain/events.py

# 4. 创建 domain/__init__.py
cat > domain/__init__.py << 'EOF'
"""Domain Layer - Pure business logic, no dependencies"""

from .library import Library, LibraryName
from .events import LibraryCreated, LibraryRenamed, LibraryDeleted

__all__ = [
    "Library",
    "LibraryName",
    "LibraryCreated",
    "LibraryRenamed",
    "LibraryDeleted",
]
EOF

# 5. 删除旧 domain.py
rm domain.py

步骤 1.2：解决 router.py 冲突
# ❌ 错误：同时存在
backend/api/app/modules/library/router.py       # 文件
backend/api/app/modules/library/routers/        # 文件夹

# ✅ 正确：
# 创建文件夹 routers/，把 router.py 的内容移到 routers/library_router.py

执行命令：
cd backend/api/app/modules/library

# 1. 备份原 router.py
cp router.py router.py.backup

# 2. 如果 routers/ 文件夹不存在，创建
mkdir -p routers

# 3. 把 router.py 的内容移到 routers/library_router.py
mv router.py routers/library_router.py

# 4. 创建 routers/__init__.py
cat > routers/__init__.py << 'EOF'
"""HTTP Adapters - FastAPI routes"""

from .library_router import router

__all__ = ["router"]
EOF

步骤 1.3：完善 application/ 层（最重要）
这是六边形架构的关键。application/ 里必须有两样：

A. Input Ports（UseCase 接口）

# backend/api/app/modules/library/application/ports/input.py

from abc import ABC, abstractmethod
from uuid import UUID
from dataclasses import dataclass

@dataclass
class CreateLibraryRequest:
    """Input DTO for CreateLibraryUseCase"""
    user_id: UUID
    name: str

@dataclass
class CreateLibraryResponse:
    """Output DTO"""
    id: UUID
    user_id: UUID
    name: str
    created_at: str

class ICreateLibraryUseCase(ABC):
    """Input Port - CreateLibrary"""
    @abstractmethod
    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse:
        pass

# 类似地定义其他 use cases...
class IGetLibraryUseCase(ABC):
    @abstractmethod
    async def execute(self, library_id: UUID) -> ...:
        pass

class IDeleteLibraryUseCase(ABC):
    @abstractmethod
    async def execute(self, library_id: UUID) -> None:
        pass

B. Output Port（Repository 接口）
# backend/api/app/modules/library/application/ports/output.py

from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from ...domain import Library

class ILibraryRepository(ABC):
    """Output Port - Repository contract"""

    @abstractmethod
    async def save(self, library: Library) -> None:
        """保存 Domain 对象到持久化层"""
        pass

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """从持久化层读取并转换为 Domain 对象"""
        pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None:
        """删除"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """按用户查找"""
        pass

C. UseCase 实现
# backend/api/app/modules/library/application/use_cases/create_library.py

from ..ports.input import ICreateLibraryUseCase, CreateLibraryRequest, CreateLibraryResponse
from ..ports.output import ILibraryRepository
from ...domain import Library

class CreateLibraryUseCase(ICreateLibraryUseCase):
    """UseCase: Create a new Library"""

    def __init__(self, repository: ILibraryRepository):
        self.repository = repository

    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse:
        # 1. 创建 Domain 对象（纯业务逻辑）
        library = Library.create(
            user_id=request.user_id,
            name=request.name
        )

        # 2. 持久化（通过抽象的 Repository）
        await self.repository.save(library)

        # 3. 返回 DTO（不暴露 Domain 对象）
        return CreateLibraryResponse(
            id=library.id,
            user_id=library.user_id,
            name=library.name,
            created_at=library.created_at.isoformat()
        )

步骤 1.4：明确每一层的职责
创建规则文档（参考用）：
# backend/api/app/modules/library/ARCHITECTURE.md

# 📐 Library Module 架构规则

## 目录结构含义

### domain/
- ✅ **职责**：纯业务逻辑（不依赖任何 framework）
- ✅ **内容**：AggregateRoot、ValueObject、DomainEvent
- ❌ **禁止**：Import 任何 ORM、HTTP、外部库
- 📝 **例**：library.py, library_name.py, events.py

### application/
- ✅ **职责**：业务用例编排（协调 Domain + Repository）
- ✅ **内容**：ports/ (接口定义) + use_cases/ (实现)
- ❌ **禁止**：直接操作数据库、HTTP 相关
- 📝 **例**：
  - ports/input.py → UseCase 接口 + DTO
  - ports/output.py → Repository 接口
  - use_cases/*.py → 各个 UseCase 实现

### routers/
- ✅ **职责**：HTTP 适配器（JSON → UseCase → JSON）
- ✅ **内容**：FastAPI 路由、输入验证、异常映射
- ❌ **禁止**：业务逻辑（应该在 Domain 或 UseCase 里）
- 📝 **例**：library_router.py

### schemas.py
- ✅ **职责**：Pydantic DTO（HTTP 请求/响应）
- ✅ **内容**：CreateLibraryRequest, LibraryResponse 等
- ❌ **禁止**：业务逻辑验证（应该在 Domain）

### exceptions.py
- ✅ **职责**：Domain 异常（业务规则违反）
- ✅ **内容**：LibraryAlreadyExistsError, LibraryNotFoundError 等
- ❌ **禁止**：HTTP 状态码（由 Router 的 exception handlers 映射）


---

## 数据流

```
HTTP Request
    ↓
Router (routers/library_router.py)
    ├─ 验证输入 (schemas.py + Pydantic)
    ├─ 调用 UseCase.execute()
    │   ↓
    │ UseCase (application/use_cases/create_library.py)
    │   ├─ 调用 Domain.create() (domain/library.py)
    │   │   ↓ Domain 纯逻辑
    │   └─ 调用 Repository.save() (interface in ports/output.py)
    │       ↓ 由 DI 注入实现 (infra/storage/library_repository_impl.py)
    ├─ 捕获异常，映射到 HTTP 状态码
    └─ 返回 Response DTO
        ↓
HTTP Response
```

---

## 新增规则

1. **永远通过 Repository 接口调用**（不直接用 SQLAlchemy）
2. **不暴露 Domain 对象给 Router**（必须用 DTO）
3. **UseCase 不做 HTTP 相关事情**（Router 的职责）
4. **Domain 不知道 Repository 的存在**（完全解耦）


Workspace
(rerun without)
Collecting workspace information

我完全理解你的困境。让我逐步梳理并给出分阶段、可执行的调整方案。


步骤 1.5：调整 __init__.py
# backend/api/app/modules/library/__init__.py

"""
Library Module - Domain-driven module with hexagonal architecture

Layers:
- domain/: Pure business logic
- application/: Use cases and ports
- routers/: HTTP adapters
- schemas.py: DTOs
- exceptions.py: Domain exceptions
- conftest.py: Test fixtures
"""

# 导出公开接口
from .domain import Library, LibraryName
from .exceptions import (
    LibraryAlreadyExistsError,
    LibraryNotFoundError,
)

__all__ = [
    "Library",
    "LibraryName",
    "LibraryAlreadyExistsError",
    "LibraryNotFoundError",
]

步骤 1.6：调整 router.py 中的导入
现在 router 从 routers/library_router.py 导入，需要更新注册代码：
# backend/api/app/main.py

from fastapi import FastAPI
from .modules.library.routers import router as library_router

app = FastAPI()

# 注册路由
app.include_router(library_router, prefix="/api/libraries", tags=["library"])

📊 Library 模块调整完成后的结构
backend/api/app/modules/library/
├── __init__.py
│
├── domain/
│   ├── __init__.py
│   ├── library.py                # Library AggregateRoot
│   ├── library_name.py           # LibraryName ValueObject
│   └── events.py                 # LibraryCreated, etc.
│
├── application/
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── input.py              # UseCase interfaces + DTO
│   │   └── output.py             # Repository interface
│   │
│   └── use_cases/
│       ├── __init__.py
│       ├── create_library.py
│       ├── get_library.py
│       ├── delete_library.py
│       └── rename_library.py
│
├── routers/
│   ├── __init__.py
│   └── library_router.py         # HTTP 路由
│
├── schemas.py                    # Pydantic DTO
├── exceptions.py                 # Domain exceptions
├── conftest.py                   # pytest fixtures
├── ARCHITECTURE.md               # 规则文档
└── models.py                     # ORM Model (保留在这里，后续迁到 infra)

🚨 第一阶段的完成标志
当 library 模块调整完毕，你应该能：
# 1. 无文件/文件夹冲突
ls backend/api/app/modules/library/
# 应该看到：application/, domain/, routers/, schemas.py, exceptions.py ...

# 2. Import 无误
python -c "from backend.api.app.modules.library import Library; print('✅ OK')"

# 3. 测试通过
pytest backend/api/app/tests/test_library/ -v
# 应该通过（或清楚地显示哪些需要调整）