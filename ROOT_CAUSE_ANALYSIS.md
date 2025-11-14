# Wordloom 四大模块测试失败根本原因分析

## 概述

经过完整的测试套件执行，共发现 **4 个根本性问题** 导致 75 个测试失败和 28 个错误。本文档详细分析每个问题的根源、影响范围和修复方案。

---

## 问题 #1: 异步测试支持缺失

### 症状
```
Failed: async def functions are not natively supported.
```

### 根本原因
- pytest 默认不支持异步函数测试
- 需要使用 `pytest-asyncio` 插件
- 当前 `pyproject.toml` 中未配置异步模式

### 影响范围
- **Library Repository**: 11/11 测试失败
- **Library Application**: 12+ 测试失败
- **Bookshelf Repository**: 8/8 测试失败
- **Bookshelf Application**: 18 个测试在初始化时错误
- **Book Application**: 27/27 测试失败
- **Book Infrastructure**: 3 个异步测试失败

**总影响**: ~46-65 个测试

### 修复方案

#### 方案 A: 配置异步模式（推荐）
编辑 `backend/pyproject.toml`:
```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["api/app/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

或在 `backend/conftest.py` 添加:
```python
import pytest

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

#### 方案 B: 使用装饰器
对每个异步测试添加 `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_save_library():
    ...
```

### 验证步骤
```bash
cd backend
pytest --co -q api/app/tests/test_library/test_repository.py
# 应显示测试被收集而非跳过
```

---

## 问题 #2: Block 模块相对导入错误

### 症状
```
ImportError: attempted relative import beyond top-level package
from ....infra.event_bus import EventType
```

### 文件位置
- `api/app/modules/block/domain/events.py` 第 12 行

### 根本原因

**导入链分析**:
```
api/app/tests/test_block/test_domain.py
  └─> from modules.block.domain import Block  ❌ 错误的导入路径
      (应为: from api.app.modules.block.domain import Block)
        └─> api/app/modules/block/domain/block.py
            └─> api/app/modules/block/domain/events.py
                └─> from ....infra.event_bus  ❌ 相对导入越界
                    (从 api/app/modules/block/domain 向上 4 级)
                    实际路径: api.app.modules.block.domain
                    相对导入变为: api/infra (超出包界限)
```

### 具体问题

1. **测试导入路径不一致**:
   - `test_domain.py` 使用: `from modules.block.domain import Block`
   - 正确应为: `from api.app.modules.block.domain import Block`

2. **相对导入链过深**:
   - `events.py` 位于: `api/app/modules/block/domain/events.py`
   - 使用 `from ....infra.event_bus` 尝试访问 `api/infra/` (不存在)
   - 正确应为: `from api.app.infra.event_bus import EventType`

### 影响范围
- Block Domain Tests: 无法收集
- Block Repository Tests: 无法收集
- Block Paperballs Recovery: 语法错误（见问题 #3）

**总影响**: Block 模块完全不可用

### 修复方案

#### 步骤 1: 修复 events.py 的导入

编辑 `backend/api/app/modules/block/domain/events.py`:

**前**:
```python
from ....infra.event_bus import EventType
from ....shared.events import DomainEvent
```

**后**:
```python
from api.app.infra.event_bus import EventType
from api.app.shared.events import DomainEvent
```

#### 步骤 2: 修复测试文件的导入

编辑 `backend/api/app/tests/test_block/test_domain.py`:

**前**:
```python
from modules.block.domain import Block, BlockContent, BlockType
```

**后**:
```python
from api.app.modules.block.domain import Block, BlockContent, BlockType
```

同样修复 `test_block/test_repository.py`

#### 步骤 3: 验证事件总线存在

检查文件: `backend/api/app/infra/event_bus.py`

如果不存在，创建最小实现:
```python
from enum import Enum

class EventType(Enum):
    BLOCK_CREATED = "block_created"
    BLOCK_UPDATED = "block_updated"
    BLOCK_DELETED = "block_deleted"
    # ... 其他事件类型
```

### 验证步骤
```bash
cd backend
python -c "from api.app.modules.block.domain import Block"
# 应无错误
```

---

## 问题 #3: Paperballs Recovery 测试语法错误

### 症状
```
SyntaxError: invalid syntax
File "test_paperballs_recovery.py", line 568
  class TestPaperballs RecoveryEdgeCases:
         ^^^^^^^^^^^^^^^^^
```

### 根本原因
Python 类名中包含空格，这在 Python 中非法。
- 类名: `TestPaperballs RecoveryEdgeCases` ❌
- 应为: `TestPaperballsRecoveryEdgeCases` ✅ 或 `TestPaperballs_RecoveryEdgeCases` ✅

### 文件位置
- `backend/api/app/tests/test_block/test_paperballs_recovery.py` 第 568 行

### 修复方案

编辑 `test_paperballs_recovery.py` 第 568 行:

**前**:
```python
class TestPaperballs RecoveryEdgeCases:
```

**后** (选项 1 - PascalCase):
```python
class TestPaperballsRecoveryEdgeCases:
```

**或后** (选项 2 - 蛇形大小写):
```python
class TestPaperballs_RecoveryEdgeCases:
```

### 验证步骤
```bash
cd backend
python -m py_compile api/app/tests/test_block/test_paperballs_recovery.py
# 应无错误
```

---

## 问题 #4: 域对象属性名不匹配

### 症状
```
AttributeError: 'Library' object has no attribute 'library_id'
TypeError: Library.__init__() got an unexpected keyword argument 'library_id'
```

### 根本原因

#### Library 聚合根
- **测试期望**: `library = Library(library_id=uuid4(), user_id=uuid4(), ...)`
- **实际实现**: Library 构造函数参数名不同

编辑 `backend/api/app/modules/library/domain/library.py`:

需要检查 `__init__` 签名:
```python
class Library:
    def __init__(self, ???):  # 参数名不匹配
        # 测试发送 library_id，但参数名可能是 id, _id 等
```

#### Bookshelf 聚合根
- 同样问题，使用了 `bookshelf_id` 测试但实现使用不同的参数名

### 影响范围
- Library Domain: 1 个测试 (test_library_creation_valid)
- Bookshelf Domain: 6 个测试 (所有使用 bookshelf_id 的)

**总影响**: 7 个测试

### 修复方案

#### 步骤 1: 审查 Library 构造函数

编辑 `backend/api/app/modules/library/domain/library.py`:

```python
from uuid import UUID
from datetime import datetime

class Library:
    def __init__(
        self,
        library_id: UUID,      # ← 确保参数名为 library_id
        user_id: UUID,
        name: 'LibraryName',
        created_at: datetime,
        updated_at: datetime,
    ):
        self._library_id = library_id
        self._user_id = user_id
        self._name = name
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def library_id(self) -> UUID:
        return self._library_id

    @property
    def user_id(self) -> UUID:
        return self._user_id
```

#### 步骤 2: 审查 Bookshelf 构造函数

编辑 `backend/api/app/modules/bookshelf/domain/bookshelf.py`:

同样确保:
```python
def __init__(
    self,
    bookshelf_id: UUID,      # ← 确保参数名为 bookshelf_id
    library_id: UUID,
    name: 'BookshelfName',
    # ...
):
```

#### 步骤 3: 验证测试预期值

确保测试代码使用一致的参数名:
```python
def test_library_creation_valid():
    library_id = uuid4()
    user_id = uuid4()

    library = Library(
        library_id=library_id,  # ← 确保参数名匹配
        user_id=user_id,
        name=LibraryName("My Library"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert library.library_id == library_id
```

### 验证步骤
```bash
cd backend
pytest api/app/tests/test_library/test_domain.py::TestLibraryAggregateRoot::test_library_creation_valid -v
# 应通过
```

---

## 问题 #5: 字符串验证逻辑缺陷

### 症状
```
AssertionError: assert '  Trimmed Name  ' == 'Trimmed Name'
ValueError: Library name cannot be empty or whitespace-only
```

### 根本原因

#### LibraryName 值对象验证
`backend/api/app/modules/library/domain/library_name.py`:

```python
class LibraryName:
    def __init__(self, value: str):
        # 问题 1: 未正确 strip
        trimmed = value.strip()

        # 问题 2: 空白检查不完整
        if not value:  # ❌ 检查原始值，不检查 trimmed
            raise ValueError("...")

        # 问题 3: 长度检查对象不一致
        if len(value) > 255:  # ❌ 检查原始值长度
            raise ValueError("...")

        self._value = trimmed  # ✅ 但最后存储的是 trimmed
```

### 测试失败的具体案例

1. **test_library_name_strip_whitespace**:
   ```python
   name = LibraryName("  Trimmed Name  ")
   assert name.value == "Trimmed Name"  # ❌ 实际返回: "  Trimmed Name  "
   ```

2. **test_library_name_empty_raises_error**:
   ```python
   with pytest.raises(ValueError):
       LibraryName("")  # ❌ 应抛出，但实际未抛出
   ```

3. **test_library_name_too_long_raises_error**:
   ```python
   long_name = "x" * 256
   with pytest.raises(ValueError):
       LibraryName(long_name)  # ❌ 长度检查不工作
   ```

### 影响范围
- Library Domain: 4 个测试
- Bookshelf Domain: 2 个测试

**总影响**: 6 个测试

### 修复方案

#### 修复 LibraryName

编辑 `backend/api/app/modules/library/domain/library_name.py`:

**前**:
```python
class LibraryName:
    def __init__(self, value: str):
        if not value:
            raise ValueError("Library name cannot be empty")
        if len(value) > 255:
            raise ValueError(f"Name too long: {len(value)}")

        self._value = value.strip()
```

**后**:
```python
class LibraryName:
    MAX_LENGTH = 255

    def __init__(self, value: str):
        # 1. 先 strip，再验证
        trimmed = value.strip()

        # 2. 检查空白
        if not trimmed:
            raise ValueError("Library name cannot be empty or whitespace-only")

        # 3. 检查长度（对 trimmed 后的值）
        if len(trimmed) > self.MAX_LENGTH:
            raise ValueError(
                f"Library name cannot exceed {self.MAX_LENGTH} characters. "
                f"Provided: {len(trimmed)} characters"
            )

        self._value = trimmed

    @property
    def value(self) -> str:
        return self._value
```

#### 修复 BookshelfName

编辑 `backend/api/app/modules/bookshelf/domain/bookshelf_name.py`:

应用相同的修复模式:
```python
class BookshelfName:
    MAX_LENGTH = 255

    def __init__(self, value: str):
        trimmed = value.strip()

        if not trimmed:
            raise ValueError("Bookshelf name cannot be empty")

        if len(trimmed) > self.MAX_LENGTH:
            raise ValueError(
                f"Bookshelf name must not exceed {self.MAX_LENGTH} characters "
                f"(got {len(trimmed)})"
            )

        self._value = trimmed
```

### 验证步骤
```bash
cd backend
pytest api/app/tests/test_library/test_domain.py::TestLibraryName -v
# 应全部通过
```

---

## 问题 #6: Mock 实现不完整

### 症状
```
TypeError: Can't instantiate abstract class MockBookshelfRepository
without an implementation for abstract method 'find_deleted_by_library'
```

### 根本原因

`BookshelfRepository` 抽象类定义了 `find_deleted_by_library` 抽象方法，但 Mock 实现未完成。

### 文件位置
- 抽象类: `backend/api/app/modules/bookshelf/domain/repository.py`
- Mock 类: `backend/api/app/tests/test_bookshelf/test_application_layer.py`

### 修复方案

编辑 `test_application_layer.py` 的 MockBookshelfRepository:

**前**:
```python
class MockBookshelfRepository:
    async def save(self, bookshelf):
        pass

    async def find_by_id(self, bookshelf_id):
        pass

    # ❌ 缺少 find_deleted_by_library
```

**后**:
```python
class MockBookshelfRepository:
    async def save(self, bookshelf):
        pass

    async def find_by_id(self, bookshelf_id):
        pass

    async def find_by_library_id(self, library_id):
        pass

    async def find_deleted_by_library(self, library_id):  # ← 新增
        return []

    async def delete(self, bookshelf_id):
        pass

    # ... 其他必需的方法
```

### 影响范围
- Bookshelf Application: 18 个测试

**总影响**: 18 个测试

### 验证步骤
```bash
cd backend
python -c "from api.app.tests.test_bookshelf.test_application_layer import MockBookshelfRepository; m = MockBookshelfRepository()"
# 应无错误
```

---

## 问题 #7: 缺失的共享模块

### 症状
```
ModuleNotFoundError: No module named 'api.app.shared.event_bus'
```

### 文件位置
- 导入失败: `backend/api/app/modules/library/application/use_cases/restore_library.py` 第 34 行
- 期望位置: `backend/api/app/shared/event_bus.py`

### 根本原因
某些 use case 依赖事件总线，但该模块未创建。

### 影响范围
- Library Application: 某些 use case 无法导入

### 修复方案

创建 `backend/api/app/shared/event_bus.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Callable
from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    LIBRARY_CREATED = "library.created"
    LIBRARY_DELETED = "library.deleted"
    BOOKSHELF_CREATED = "bookshelf.created"
    BOOKSHELF_DELETED = "bookshelf.deleted"
    BOOK_CREATED = "book.created"
    BOOK_DELETED = "book.deleted"
    BLOCK_CREATED = "block.created"
    # ... 其他事件类型


class Event(ABC):
    """事件基类"""

    @property
    @abstractmethod
    def event_type(self) -> EventType:
        pass


class EventBus:
    """事件总线"""

    def __init__(self):
        self._subscribers: dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """发布事件"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
```

---

## 优先级修复顺序

### Phase 1: 基础设施修复（1 小时）
1. ✅ 启用异步测试支持 (修复 46+ 个测试)
2. ✅ 修复 Block 相对导入 (恢复模块可用性)
3. ✅ 修复 Paperballs 类名语法 (恢复模块可用性)

### Phase 2: 验证修复（30 分钟）
1. ✅ 修复属性名不匹配 (修复 7 个测试)
2. ✅ 修复字符串验证逻辑 (修复 6 个测试)
3. ✅ 完善 Mock 实现 (修复 18 个测试)

### Phase 3: 缺失模块（20 分钟）
1. ✅ 创建事件总线模块
2. ✅ 验证所有导入

---

## 最终验证清单

```bash
# 1. 验证异步支持
pytest --co -q api/app/tests/test_library/test_repository.py | head -5

# 2. 验证 Block 导入
python -c "from api.app.modules.block.domain import Block"

# 3. 验证类名语法
python -m py_compile api/app/tests/test_block/test_paperballs_recovery.py

# 4. 验证属性
pytest api/app/tests/test_library/test_domain.py::TestLibraryAggregateRoot::test_library_creation_valid -v

# 5. 验证字符串验证
pytest api/app/tests/test_library/test_domain.py::TestLibraryName -v

# 6. 验证 Mock
python -c "from api.app.tests.test_bookshelf.test_application_layer import MockBookshelfRepository; m = MockBookshelfRepository()"

# 7. 完整测试运行
pytest api/app/tests/ -v --tb=short 2>&1 | tee final_test_report.txt
```

---

**分析文档版本**: 1.0
**生成时间**: 2025-11-14
**分析范围**: 172 个测试，4 个核心根本问题
