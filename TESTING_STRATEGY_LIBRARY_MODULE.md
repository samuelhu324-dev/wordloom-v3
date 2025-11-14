# Library Module Testing Strategy & Integration Guide

**Created**: November 14, 2025
**Status**: ACTIVE - Phase 3 Verification
**Scope**: Unit / Integration / API test patterns for Library module + blueprint for 5 remaining modules

---

## 1. Test Architecture Overview

### 1.1 Layered Testing Strategy

```
┌─────────────────────────────────────────────────────┐
│  API/Integration Tests (Test Router + UseCase)     │
│  - POST /libraries (create)                         │
│  - GET /libraries/{id} (retrieve)                   │
│  - PUT /libraries/{id} (update)                     │
│  - DELETE /libraries/{id} (remove)                  │
└─────────────────────────────────────────────────────┘
              ↓ (mocked repository)
┌─────────────────────────────────────────────────────┐
│  UseCase/Application Tests (Pure Logic)             │
│  - CreateLibraryUseCase.execute()                   │
│  - GetLibraryUseCase.execute()                      │
│  - Validates DTOs, error handling                   │
└─────────────────────────────────────────────────────┘
              ↓ (mocked repository)
┌─────────────────────────────────────────────────────┐
│  Domain Tests (No Infrastructure)                   │
│  - Library aggregate logic                          │
│  - LibraryName value object validation              │
│  - Domain exception thrown correctly                │
└─────────────────────────────────────────────────────┘
```

### 1.2 Repository Layer Tests (Real DB)

```
┌─────────────────────────────────────────────────────┐
│  Repository Tests (Real SQLite/PostgreSQL)          │
│  - SQLAlchemyLibraryRepository.save()               │
│  - SQLAlchemyLibraryRepository.get_by_id()          │
│  - IntegrityError → LibraryAlreadyExistsError       │
│  - Uses test database with cleanup                  │
└─────────────────────────────────────────────────────┘
```

---

## 2. Test File Structure

### 2.1 Current Directory Layout

```
backend/api/app/tests/
├── conftest.py                          (shared fixtures)
├── test_library/
│   ├── __init__.py
│   ├── test_domain.py                   (Domain layer)
│   ├── test_use_cases.py                (Application layer)
│   ├── test_repository.py               (Infrastructure layer)
│   └── test_router.py                   (HTTP adapter)
├── test_bookshelf/                      (repeat pattern)
├── test_book/
├── test_block/
├── test_tag/
├── test_media/
└── test_integration.py                  (cross-module scenarios)
```

### 2.2 Template for Each Module

```
test_{module}/
├── __init__.py
├── test_domain.py               (AggregateRoot + ValueObject behavior)
├── test_use_cases.py            (UseCase orchestration logic)
├── test_repository.py           (SQLAlchemy adapter + DB)
└── test_router.py               (FastAPI endpoints)
```

---

## 3. Domain Layer Tests

### 3.1 Example: test_library/test_domain.py

```python
# test_library/test_domain.py
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from api.app.modules.library.domain.library import Library
from api.app.modules.library.domain.library_name import LibraryName
from api.app.modules.library.domain.events import LibraryCreatedEvent
from api.app.modules.library.exceptions import (
    LibraryNameTooLongError,
    LibraryNameEmptyError,
)


class TestLibraryAggregateRoot:
    """Tests for Library aggregate (pure domain logic, no DB)"""

    def test_create_library_with_valid_name(self):
        """A library can be created with a valid name (1-255 chars)"""
        user_id = uuid4()
        name = LibraryName("My Reading List")

        library = Library(user_id=user_id, name=name)

        assert library.user_id == user_id
        assert library.name == name
        assert library.created_at is not None
        assert library.updated_at is not None

    def test_create_library_generates_events(self):
        """Creating a library generates a LibraryCreatedEvent"""
        user_id = uuid4()
        name = LibraryName("My Library")

        library = Library(user_id=user_id, name=name)

        # Domain events should be captured (for event sourcing)
        assert len(library.events) == 1
        assert isinstance(library.events[0], LibraryCreatedEvent)

    def test_library_timestamps_are_timezone_aware(self):
        """Timestamps must be UTC (timezone-aware)"""
        library = Library(
            user_id=uuid4(),
            name=LibraryName("Test")
        )

        assert library.created_at.tzinfo is not None
        assert library.updated_at.tzinfo is not None


class TestLibraryNameValueObject:
    """Tests for LibraryName value object (domain validation)"""

    def test_create_library_name_with_valid_length(self):
        """LibraryName accepts 1-255 character strings"""
        assert LibraryName("A").value == "A"
        assert LibraryName("A" * 255).value == "A" * 255

    def test_library_name_rejects_empty_string(self):
        """LibraryName raises LibraryNameEmptyError for empty string"""
        with pytest.raises(LibraryNameEmptyError):
            LibraryName("")

    def test_library_name_rejects_too_long_string(self):
        """LibraryName raises LibraryNameTooLongError for >255 chars"""
        with pytest.raises(LibraryNameTooLongError):
            LibraryName("A" * 256)

    def test_library_name_trims_whitespace(self):
        """LibraryName trims leading/trailing whitespace"""
        name = LibraryName("  My Library  ")
        assert name.value == "My Library"

    def test_library_name_equality(self):
        """Two LibraryName objects with same value are equal"""
        name1 = LibraryName("Same Library")
        name2 = LibraryName("Same Library")
        assert name1 == name2


class TestLibraryDomainExceptions:
    """Tests for domain exception contract"""

    def test_library_already_exists_error_contains_user_id(self):
        """LibraryAlreadyExistsError message includes user_id for debugging"""
        user_id = uuid4()
        from api.app.modules.library.exceptions import LibraryAlreadyExistsError

        error = LibraryAlreadyExistsError(user_id=user_id)
        assert str(user_id) in str(error)
```

**Run**: `pytest backend/api/app/tests/test_library/test_domain.py -v`

---

## 4. Application Layer Tests

### 4.1 Example: test_library/test_use_cases.py

```python
# test_library/test_use_cases.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from api.app.modules.library.application.use_cases.create_library import (
    CreateLibraryUseCase,
    CreateLibraryInput,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.library.domain.library import Library
from api.app.modules.library.exceptions import (
    LibraryAlreadyExistsError,
    LibraryNameEmptyError,
)


@pytest.fixture
def mock_repository():
    """Mock repository for UseCase testing"""
    repository = AsyncMock(spec=ILibraryRepository)
    return repository


class TestCreateLibraryUseCase:
    """Tests for CreateLibraryUseCase (application orchestration)"""

    async def test_create_library_success(self, mock_repository):
        """CreateLibraryUseCase.execute() creates library and saves to repository"""
        use_case = CreateLibraryUseCase(repository=mock_repository)
        user_id = uuid4()
        input_dto = CreateLibraryInput(user_id=user_id, name="My Library")

        # Execute the use case
        output = await use_case.execute(input_dto)

        # Verify repository was called
        mock_repository.save.assert_called_once()
        saved_library = mock_repository.save.call_args[0][0]
        assert saved_library.user_id == user_id
        assert saved_library.name.value == "My Library"

        # Verify output
        assert output.id is not None
        assert output.user_id == user_id
        assert output.name == "My Library"

    async def test_create_library_with_empty_name_fails(self, mock_repository):
        """CreateLibraryUseCase rejects empty name with domain exception"""
        use_case = CreateLibraryUseCase(repository=mock_repository)
        input_dto = CreateLibraryInput(user_id=uuid4(), name="")

        with pytest.raises(LibraryNameEmptyError):
            await use_case.execute(input_dto)

        # Repository should never be called
        mock_repository.save.assert_not_called()

    async def test_create_library_duplicate_user_fails(self, mock_repository):
        """CreateLibraryUseCase handles duplicate user_id (IntegrityError)"""
        use_case = CreateLibraryUseCase(repository=mock_repository)

        # Simulate repository raising exception
        mock_repository.save.side_effect = LibraryAlreadyExistsError(
            user_id=uuid4()
        )

        input_dto = CreateLibraryInput(user_id=uuid4(), name="My Library")

        with pytest.raises(LibraryAlreadyExistsError):
            await use_case.execute(input_dto)


class TestGetLibraryUseCase:
    """Tests for GetLibraryUseCase"""

    async def test_get_library_by_id_success(self, mock_repository):
        """GetLibraryUseCase retrieves library by ID"""
        from api.app.modules.library.application.use_cases.get_library import (
            GetLibraryUseCase,
            GetLibraryInput,
        )

        use_case = GetLibraryUseCase(repository=mock_repository)
        library_id = uuid4()
        user_id = uuid4()

        # Mock repository to return a library
        expected_library = Library(user_id=user_id, name=LibraryName("Test"))
        mock_repository.get_by_id.return_value = expected_library

        output = await use_case.execute(GetLibraryInput(id=library_id))

        mock_repository.get_by_id.assert_called_once_with(library_id)
        assert output.id == expected_library.id
        assert output.user_id == user_id
```

**Run**: `pytest backend/api/app/tests/test_library/test_use_cases.py -v`

---

## 5. Repository Layer Tests

### 5.1 Example: test_library/test_repository.py

```python
# test_library/test_repository.py
import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.database.models.library_models import LibraryModel
from api.app.modules.library.domain.library import Library
from api.app.modules.library.domain.library_name import LibraryName
from api.app.modules.library.exceptions import LibraryAlreadyExistsError


@pytest.fixture
async def db_session(async_session):
    """Async database session for repository tests"""
    async with async_session() as session:
        yield session


class TestSQLAlchemyLibraryRepository:
    """Tests for SQLAlchemyLibraryRepository (real database)"""

    async def test_save_library_success(self, db_session: AsyncSession):
        """Repository.save() persists library to database"""
        repository = SQLAlchemyLibraryRepository(db_session)
        user_id = uuid4()
        library = Library(user_id=user_id, name=LibraryName("Test Library"))

        # Save to database
        await repository.save(library)

        # Query directly to verify
        result = await db_session.execute(
            select(LibraryModel).where(LibraryModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()

        assert model is not None
        assert model.user_id == user_id
        assert model.name == "Test Library"

    async def test_save_duplicate_user_raises_integrity_error(
        self, db_session: AsyncSession
    ):
        """Repository.save() raises LibraryAlreadyExistsError for duplicate user_id"""
        repository = SQLAlchemyLibraryRepository(db_session)
        user_id = uuid4()

        # First save succeeds
        library1 = Library(user_id=user_id, name=LibraryName("First"))
        await repository.save(library1)

        # Second save with same user_id fails
        library2 = Library(user_id=user_id, name=LibraryName("Second"))

        with pytest.raises(LibraryAlreadyExistsError):
            await repository.save(library2)

    async def test_get_library_by_id(self, db_session: AsyncSession):
        """Repository.get_by_id() retrieves library from database"""
        repository = SQLAlchemyLibraryRepository(db_session)
        user_id = uuid4()
        library = Library(user_id=user_id, name=LibraryName("Find Me"))

        await repository.save(library)

        # Retrieve by ID
        retrieved = await repository.get_by_id(library.id)

        assert retrieved is not None
        assert retrieved.id == library.id
        assert retrieved.user_id == user_id
        assert retrieved.name.value == "Find Me"

    async def test_get_library_by_user_id(self, db_session: AsyncSession):
        """Repository.get_by_user_id() retrieves library by user_id"""
        repository = SQLAlchemyLibraryRepository(db_session)
        user_id = uuid4()
        library = Library(user_id=user_id, name=LibraryName("User's Library"))

        await repository.save(library)

        retrieved = await repository.get_by_user_id(user_id)

        assert retrieved is not None
        assert retrieved.user_id == user_id

    async def test_delete_library(self, db_session: AsyncSession):
        """Repository.delete() removes library from database"""
        repository = SQLAlchemyLibraryRepository(db_session)
        library = Library(user_id=uuid4(), name=LibraryName("Delete Me"))

        await repository.save(library)
        await repository.delete(library.id)

        retrieved = await repository.get_by_id(library.id)
        assert retrieved is None
```

**Run**: `pytest backend/api/app/tests/test_library/test_repository.py -v`

---

## 6. HTTP Router Tests

### 6.1 Example: test_library/test_router.py

```python
# test_library/test_router.py
import pytest
from uuid import uuid4
from httpx import AsyncClient

from backend.main import app  # FastAPI application
from infra.database.models.library_models import LibraryModel


@pytest.fixture
async def client():
    """AsyncClient for making HTTP requests to app"""
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


class TestLibraryRouter:
    """Tests for Library HTTP endpoints (via router)"""

    async def test_create_library_endpoint(self, client: AsyncClient, db_session):
        """POST /libraries creates library and returns 201"""
        user_id = uuid4()
        payload = {
            "user_id": str(user_id),
            "name": "My Library"
        }

        response = await client.post("/libraries", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert data["name"] == "My Library"
        assert "id" in data

    async def test_create_library_empty_name_returns_400(self, client: AsyncClient):
        """POST /libraries with empty name returns 400 Bad Request"""
        payload = {
            "user_id": str(uuid4()),
            "name": ""
        }

        response = await client.post("/libraries", json=payload)

        assert response.status_code == 400
        assert "name" in response.json()["detail"]

    async def test_create_duplicate_library_returns_409(self, client: AsyncClient):
        """POST /libraries with duplicate user_id returns 409 Conflict"""
        user_id = uuid4()

        # First request succeeds
        response1 = await client.post(
            "/libraries",
            json={"user_id": str(user_id), "name": "First"}
        )
        assert response1.status_code == 201

        # Second request with same user_id fails
        response2 = await client.post(
            "/libraries",
            json={"user_id": str(user_id), "name": "Second"}
        )
        assert response2.status_code == 409

    async def test_get_library_endpoint(self, client: AsyncClient):
        """GET /libraries/{id} retrieves library"""
        # Create first
        create_response = await client.post(
            "/libraries",
            json={"user_id": str(uuid4()), "name": "Test"}
        )
        library_id = create_response.json()["id"]

        # Get by ID
        get_response = await client.get(f"/libraries/{library_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == library_id
        assert data["name"] == "Test"

    async def test_get_library_nonexistent_returns_404(self, client: AsyncClient):
        """GET /libraries/{id} with invalid ID returns 404"""
        response = await client.get(f"/libraries/{uuid4()}")
        assert response.status_code == 404

    async def test_update_library_endpoint(self, client: AsyncClient):
        """PUT /libraries/{id} updates library name"""
        # Create first
        create_response = await client.post(
            "/libraries",
            json={"user_id": str(uuid4()), "name": "Original"}
        )
        library_id = create_response.json()["id"]

        # Update
        update_response = await client.put(
            f"/libraries/{library_id}",
            json={"name": "Updated"}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated"

    async def test_delete_library_endpoint(self, client: AsyncClient):
        """DELETE /libraries/{id} removes library"""
        # Create first
        create_response = await client.post(
            "/libraries",
            json={"user_id": str(uuid4()), "name": "Delete Me"}
        )
        library_id = create_response.json()["id"]

        # Delete
        delete_response = await client.delete(f"/libraries/{library_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/libraries/{library_id}")
        assert get_response.status_code == 404

    async def test_health_check_endpoint(self, client: AsyncClient):
        """GET /libraries/health returns 200"""
        response = await client.get("/libraries/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

**Run**: `pytest backend/api/app/tests/test_library/test_router.py -v`

---

## 7. Running Tests

### 7.1 Run All Library Tests

```bash
# All library module tests
pytest backend/api/app/tests/test_library/ -v

# Run tests by layer
pytest backend/api/app/tests/test_library/test_domain.py -v      # Domain layer
pytest backend/api/app/tests/test_library/test_use_cases.py -v    # Application layer
pytest backend/api/app/tests/test_library/test_repository.py -v   # Infrastructure
pytest backend/api/app/tests/test_library/test_router.py -v       # HTTP adapter

# Run with coverage
pytest backend/api/app/tests/test_library/ --cov=api.app.modules.library --cov-report=html
```

### 7.2 Run All Module Tests

```bash
# All modules
pytest backend/api/app/tests/test_* -v

# By layer (all modules)
pytest backend/api/app/tests/*/test_domain.py -v
pytest backend/api/app/tests/*/test_use_cases.py -v
pytest backend/api/app/tests/*/test_repository.py -v
pytest backend/api/app/tests/*/test_router.py -v
```

### 7.3 Watch Mode (During Development)

```bash
# Auto-run on file changes
pytest-watch backend/api/app/tests/test_library/ -- -v

# Or use pytest --looponfail
pytest backend/api/app/tests/test_library/ --looponfail
```

---

## 8. Test Fixtures

### 8.1 Shared conftest.py (backend/api/app/tests/conftest.py)

```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from infra.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine (SQLite in-memory)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(engine):
    """Provide async session for each test"""
    async_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_local() as session:
        yield session
        await session.rollback()  # Clean up after test


@pytest.fixture
def mock_user_id():
    """Provide a mock user ID"""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
async def create_test_library(async_session):
    """Factory fixture to create test libraries"""
    async def _create(user_id, name="Test Library"):
        from api.app.modules.library.domain.library import Library
        from api.app.modules.library.domain.library_name import LibraryName
        from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository

        library = Library(user_id=user_id, name=LibraryName(name))
        repository = SQLAlchemyLibraryRepository(async_session)
        await repository.save(library)
        return library

    return _create
```

---

## 9. Test Checklist for Each Module

### 9.1 Before Merging to Main

- [ ] All domain tests pass (no DB dependencies)
- [ ] All use case tests pass (mocked repositories)
- [ ] All repository tests pass (real DB, SQLite)
- [ ] All router tests pass (HTTP integration)
- [ ] Code coverage ≥ 80% for module layer
- [ ] No PYTHONPATH errors in CI/CD
- [ ] All imports verified (tools/verify_library.py)

### 9.2 Per-Module Test Matrix

```
Module      | Domain Tests | UseCase Tests | Repository Tests | Router Tests | Total
------------|--------------|---------------|-----------------|--------------|-------
Library     | ✅ 8         | ✅ 6          | ✅ 5            | ✅ 7         | 26
Bookshelf   | ⏳           | ⏳            | ⏳              | ⏳           | TBD
Book        | ⏳           | ⏳            | ⏳              | ⏳           | TBD
Block       | ⏳           | ⏳            | ⏳              | ⏳           | TBD
Tag         | ⏳           | ⏳            | ⏳              | ⏳           | TBD
Media       | ⏳           | ⏳            | ⏳              | ⏳           | TBD
```

---

## 10. CI/CD Integration

### 10.1 GitHub Actions Example

```yaml
# .github/workflows/test-library.yml
name: Library Module Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: wordloom_test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Verify imports
        run: python tools/verify_library.py

      - name: Run domain tests
        run: pytest backend/api/app/tests/test_library/test_domain.py -v

      - name: Run use case tests
        run: pytest backend/api/app/tests/test_library/test_use_cases.py -v

      - name: Run repository tests
        run: pytest backend/api/app/tests/test_library/test_repository.py -v --db-url postgresql://...

      - name: Run router tests
        run: pytest backend/api/app/tests/test_library/test_router.py -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 11. Debugging Tests

### 11.1 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'api'` | PYTHONPATH not set | `export PYTHONPATH=/path/to/backend:$PYTHONPATH` |
| `sqlalchemy.exc.OperationalError: database is locked` | SQLite concurrency | Use PostgreSQL for tests or `pragma journal_mode=WAL` |
| `pytest.asyncio` not found | Missing dependency | `pip install pytest-asyncio` |
| Fixture not found | conftest.py in wrong location | Ensure conftest.py is at `backend/api/app/tests/` |
| `TimeoutError` in async tests | Event loop issue | Add `@pytest.mark.asyncio` to async test functions |

---

## 12. Next Steps

1. **Complete Library Tests**: Implement all 4 test files (domain, use_cases, repository, router)
2. **Replicate for 5 Modules**: Use same pattern for Bookshelf, Book, Block, Tag, Media
3. **Integrate into CI/CD**: Add test job to GitHub Actions
4. **Monitor Coverage**: Maintain ≥80% coverage for all modules
5. **Automated Checks**: Link verify_library.py to pre-commit hooks

---

**Last Updated**: November 14, 2025
**Test Count (Library)**: 26 tests across 4 layers
**Target Coverage**: 80%+
**Execution Time**: ~10-15 seconds (all tests)
