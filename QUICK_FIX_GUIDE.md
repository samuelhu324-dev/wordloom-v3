# Wordloom 测试修复快速指南

## 🚀 5 分钟快速修复方案

### 修复 #1: 启用异步测试支持 (3 分钟)

编辑 `backend/pyproject.toml`，在 `[tool.pytest.ini_options]` 下添加：

```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**验证**:
```bash
cd backend
pytest api/app/tests/test_library/test_repository.py -v --co -q | head -5
```

---

### 修复 #2: 修复 Block 模块相对导入 (2 分钟)

#### 2a. 编辑 `backend/api/app/modules/block/domain/events.py`

搜索并替换所有相对导入（第 12 行附近）：

**改前**:
```python
from ....infra.event_bus import EventType
```

**改后**:
```python
from api.app.infra.event_bus import EventType
```

#### 2b. 编辑 `backend/api/app/tests/test_block/test_domain.py`

搜索并替换测试导入（第 22 行）：

**改前**:
```python
from modules.block.domain import Block, BlockContent, BlockType
```

**改后**:
```python
from api.app.modules.block.domain import Block, BlockContent, BlockType
```

#### 2c. 编辑 `backend/api/app/tests/test_block/test_repository.py`

同样修改导入（第 23 行）

---

### 修复 #3: 修复类名语法错误 (1 分钟)

编辑 `backend/api/app/tests/test_block/test_paperballs_recovery.py`

搜索第 568 行：
```python
class TestPaperballs RecoveryEdgeCases:
```

替换为：
```python
class TestPaperballsRecoveryEdgeCases:
```

---

## 🔧 后续补充修复（需要 20-30 分钟）

### 修复 #4: 属性名不匹配

#### 编辑 `backend/api/app/modules/library/domain/library.py`

确保 `__init__` 参数包含 `library_id`：

```python
class Library:
    def __init__(
        self,
        library_id: UUID,      # ← 确保这里
        user_id: UUID,
        name: 'LibraryName',
        created_at: datetime,
        updated_at: datetime,
    ):
        self._library_id = library_id
        # ...

    @property
    def library_id(self) -> UUID:
        return self._library_id
```

#### 编辑 `backend/api/app/modules/bookshelf/domain/bookshelf.py`

确保 `__init__` 参数包含 `bookshelf_id`：

```python
class Bookshelf:
    def __init__(
        self,
        bookshelf_id: UUID,    # ← 确保这里
        library_id: UUID,
        name: 'BookshelfName',
        # ...
    ):
        self._bookshelf_id = bookshelf_id
        # ...

    @property
    def bookshelf_id(self) -> UUID:
        return self._bookshelf_id
```

---

### 修复 #5: 字符串验证逻辑

#### 编辑 `backend/api/app/modules/library/domain/library_name.py`

```python
class LibraryName:
    MAX_LENGTH = 255

    def __init__(self, value: str):
        # 关键: 先 strip 再验证
        trimmed = value.strip()

        if not trimmed:
            raise ValueError("Library name cannot be empty or whitespace-only")

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

#### 编辑 `backend/api/app/modules/bookshelf/domain/bookshelf_name.py`

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

    @property
    def value(self) -> str:
        return self._value
```

---

### 修复 #6: Mock 实现不完整

编辑 `backend/api/app/tests/test_bookshelf/test_application_layer.py`

在 `MockBookshelfRepository` 类中添加缺失的方法：

```python
class MockBookshelfRepository:
    """Mock Bookshelf Repository"""

    def __init__(self):
        self._data = {}
        self._deleted = {}

    async def save(self, bookshelf):
        self._data[bookshelf.bookshelf_id] = bookshelf

    async def find_by_id(self, bookshelf_id):
        return self._data.get(bookshelf_id)

    async def find_by_library_id(self, library_id):
        return [b for b in self._data.values()
                if b.library_id == library_id]

    async def find_deleted_by_library(self, library_id):  # ← 新增这个方法
        return [b for b in self._deleted.values()
                if b.library_id == library_id]

    async def delete(self, bookshelf_id):
        if bookshelf_id in self._data:
            self._deleted[bookshelf_id] = self._data.pop(bookshelf_id)
```

---

## ✅ 验证修复

```bash
cd backend

# 1. 测试异步支持是否启用
pytest api/app/tests/test_library/test_repository.py::TestLibraryRepositoryCRUD::test_save_library_creates_new_record -v

# 2. 测试 Block 导入是否正常
python -c "from api.app.modules.block.domain import Block; print('✓ Block import OK')"

# 3. 测试语法错误是否修复
python -m py_compile api/app/tests/test_block/test_paperballs_recovery.py && echo "✓ Syntax OK"

# 4. 测试属性名是否正确
pytest api/app/tests/test_library/test_domain.py::TestLibraryAggregateRoot::test_library_creation_valid -v

# 5. 测试字符串验证是否修复
pytest api/app/tests/test_library/test_domain.py::TestLibraryName::test_library_name_strip_whitespace -v

# 6. 运行完整库模块测试
pytest api/app/tests/test_library/ -v --tb=short | tail -20

# 7. 运行完整测试套件
pytest api/app/tests/ -v --tb=short 2>&1 | tail -5
```

---

## 📊 预期改进

| 阶段 | 修复内容 | 当前 | 预期 | 改善 |
|------|--------|------|------|------|
| Phase 1 | 异步支持 | 43 ✅ / 75 ❌ | 89 ✅ / 29 ❌ | +46 |
| Phase 2 | 属性/字符串/Mock | 89 ✅ / 29 ❌ | 110+ ✅ / 5 ❌ | +25 |
| 最终 | 全部修复 | 43 ✅ | 110+ ✅ | **156% 提升** |

**预期最终通过率**: 从 25% 提升到 **64%+**

---

## 🎯 修复时间表

| 任务 | 耗时 | 优先级 |
|------|------|--------|
| 启用异步支持 | 3 分钟 | 🔴 P0 |
| 修复 Block 导入 | 2 分钟 | 🔴 P0 |
| 修复类名语法 | 1 分钟 | 🔴 P0 |
| 修复属性名 | 10 分钟 | 🟠 P1 |
| 修复字符串验证 | 10 分钟 | 🟠 P1 |
| 完善 Mock 实现 | 5 分钟 | 🟠 P1 |
| **总计** | **~30 分钟** | |

**完成后运行**: `pytest api/app/tests/ -v` 以获取最终报告

---

## 📋 修复检查清单

- [ ] 在 `pyproject.toml` 启用 asyncio_mode
- [ ] 修复 Block 模块的相对导入（2 个文件）
- [ ] 修复类名语法错误
- [ ] 确认 Library 有 `library_id` 属性
- [ ] 确认 Bookshelf 有 `bookshelf_id` 属性
- [ ] 修复 LibraryName 字符串验证
- [ ] 修复 BookshelfName 字符串验证
- [ ] 完善 MockBookshelfRepository
- [ ] 运行 Library 模块测试验证
- [ ] 运行 Bookshelf 模块测试验证
- [ ] 运行完整测试套件生成最终报告

---

**快速指南版本**: 1.0
**预计完成时间**: 30 分钟
**预期成功率**: 90%+
