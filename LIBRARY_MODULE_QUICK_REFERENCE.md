# Library Module - Architecture Quick Reference (Nov 14, 2025)

## Structure Overview

```
api/app/modules/library/                 ← Application layer (Business logic)
├── domain/                               ← Pure domain logic (NO infra dependencies)
│   ├── library.py                       ← AggregateRoot: Library(id, user_id, name, ...)
│   ├── library_name.py                  ← ValueObject: LibraryName(value: str) [1-255 chars]
│   └── events.py                        ← DomainEvents: LibraryCreated, Renamed, Deleted
│
├── application/                          ← UseCase layer (Orchestration)
│   ├── ports/
│   │   ├── input.py                     ← Input ports: ICreateLibraryUseCase, IGetLibraryUseCase, ...
│   │   │                                  + DTOs: CreateLibraryRequest/Response, GetLibraryRequest/Response, ...
│   │   └── output.py                    ← Output port: ILibraryRepository
│   │
│   └── use_cases/
│       ├── create_library.py            ← CreateLibraryUseCase(repository: ILibraryRepository)
│       ├── get_library.py               ← GetLibraryUseCase(repository: ILibraryRepository)
│       └── delete_library.py            ← DeleteLibraryUseCase(repository: ILibraryRepository)
│
├── routers/                              ← HTTP Adapter (FastAPI)
│   └── library_router.py                ← 6 endpoints: POST, GET (id), GET (user), PUT, DELETE, health
│
├── exceptions.py                         ← Custom exceptions (LibraryAlreadyExistsError, etc.)
├── schemas.py                            ← Pydantic DTOs for HTTP (LibraryCreate, LibraryResponse, ...)
└── __init__.py                          ← Public API: exports all Domain, UseCase, Exception classes

backend/infra/                            ← Infrastructure layer (Implementation details)
├── database/
│   └── models/
│       └── library_models.py            ← SQLAlchemy ORM: LibraryModel, tables, constraints
│
└── storage/
    └── library_repository_impl.py       ← SQLAlchemyLibraryRepository implements ILibraryRepository
```

## Data Flow

### Create Library (POST /api/v1/libraries)

```
HTTP Request
    ↓
FastAPI Route (library_router.py)
    ├─ Extract user_id from JWT
    ├─ Parse request body as LibraryCreate schema
    └─ Inject CreateLibraryUseCase via DI
        ↓
CreateLibraryUseCase.execute()
    ├─ Convert HTTP request to CreateLibraryRequest DTO
    ├─ Check: existing = await repository.get_by_user_id(user_id) [RULE-001]
    │   If exists: raise LibraryAlreadyExistsError → HTTP 409
    ├─ Create domain: library = Library.create(user_id, name) [RULE-003 validation]
    ├─ Persist: await repository.save(library)
    │   └─ SQLAlchemyLibraryRepository converts Library → LibraryModel → INSERT
    └─ Return CreateLibraryResponse (DTO)
        ↓
FastAPI Route converts to LibraryResponse (Pydantic model)
    ↓
HTTP Response (201 Created)
```

## Key DDD Rules

| Rule | Enforcement | Implementation |
|------|-------------|-----------------|
| RULE-001: 1 user = 1 Library | Domain check + DB UNIQUE constraint | CreateLibraryUseCase.execute() checks get_by_user_id() |
| RULE-002: user_id NOT NULL | Pydantic validation + NOT NULL constraint | Domain factory requires UUID |
| RULE-003: name 1-255 chars | LibraryName ValueObject validation | Domain factory validates during Library.create() |

## Import Patterns

```python
# ✅ In router (library_router.py):
from modules.library.application.use_cases.create_library import CreateLibraryUseCase
from modules.library.application.ports.input import CreateLibraryRequest
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.database import get_db_session

# ✅ In UseCase (create_library.py):
from modules.library.domain.library import Library
from modules.library.application.ports.output import ILibraryRepository

# ✅ In Repository adapter (library_repository_impl.py):
from modules.library.domain.library import Library  # Domain only (no ORM here!)
from infra.database.models.library_models import LibraryModel  # ORM only here
from modules.library.application.ports.output import ILibraryRepository

# ❌ NEVER in domain layer:
# from infra.database.models.library_models import LibraryModel  # ORM leaks!
# from sqlalchemy import Column, String  # Infrastructure details!
```

## Dependency Injection Pattern

```python
# In router:
async def get_create_library_usecase(
    session: AsyncSession = Depends(get_db_session),  # FastAPI dependency
) -> CreateLibraryUseCase:
    # Infrastructure layer: create adapter
    repository = SQLAlchemyLibraryRepository(session)

    # Application layer: inject adapter into UseCase
    use_case = CreateLibraryUseCase(repository=repository)

    return use_case

# In endpoint:
@router.post("")
async def create_library(
    request: LibraryCreate,
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateLibraryUseCase = Depends(get_create_library_usecase),
) -> LibraryResponse:
    # UseCase orchestrates domain logic + persistence
    uc_request = CreateLibraryRequest(user_id=user_id, name=request.name)
    uc_response = await use_case.execute(uc_request)
    return LibraryResponse.from_response(uc_response)
```

## Testing Strategy

### Unit Test (Domain + UseCase)
```python
# No database needed, mock repository
def test_create_library_rule_001():
    """RULE-001: Each user can only have one Library"""
    mock_repo = MockLibraryRepository()
    mock_repo.libraries = [Library(id=UUID(...), user_id=user_id, name="Existing")]

    use_case = CreateLibraryUseCase(repository=mock_repo)

    with pytest.raises(LibraryAlreadyExistsError):
        await use_case.execute(CreateLibraryRequest(user_id, "New Library"))
```

### Integration Test (Full Stack)
```python
# With real database
async def test_create_library_http(client: AsyncClient, db_session: AsyncSession):
    """Full HTTP endpoint test"""
    response = await client.post(
        "/api/v1/libraries",
        json={"name": "Test Library"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Library"
```

## Exception Handling

```python
try:
    uc_response = await use_case.execute(uc_request)
except LibraryAlreadyExistsError as exc:
    # 409 Conflict
    raise HTTPException(status_code=409, detail=exc.to_dict())
except InvalidLibraryNameError as exc:
    # 422 Unprocessable Entity
    raise HTTPException(status_code=422, detail=exc.to_dict())
except LibraryException as exc:
    # Generic library error
    raise HTTPException(status_code=exc.http_status, detail=exc.to_dict())
```

## API Endpoints

| Method | Path | Description | Status Code |
|--------|------|-------------|-------------|
| POST | `/api/v1/libraries` | Create new Library | 201 / 409 / 422 |
| GET | `/api/v1/libraries/{library_id}` | Get by ID | 200 / 404 |
| GET | `/api/v1/libraries/user/{user_id}` | Get for user (RULE-001) | 200 / 404 |
| PUT | `/api/v1/libraries/{library_id}` | Update Library | 200 / 403 / 404 |
| DELETE | `/api/v1/libraries/{library_id}` | Delete (soft delete) | 204 / 403 / 404 |
| GET | `/api/v1/libraries/health` | Health check | 200 |

## ORM Model Mapping

```python
# Domain model (library.py):
@dataclass(frozen=True)
class Library:
    library_id: UUID
    user_id: UUID
    name: LibraryName  # ValueObject
    basement_bookshelf_id: UUID
    created_at: datetime
    updated_at: datetime
    soft_deleted_at: Optional[datetime]

# ORM model (library_models.py):
class LibraryModel(Base):
    __tablename__ = "libraries"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), NOT NULL, UNIQUE)  # RULE-002 + RULE-001
    name = Column(VARCHAR(255), NOT NULL)  # RULE-003
    basement_bookshelf_id = Column(UUID, ForeignKey("bookshelves.id"))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    soft_deleted_at = Column(DateTime(timezone=True), nullable=True)

# Conversion in repository (library_repository_impl.py):
def _to_domain(self, model: LibraryModel) -> Library:
    return Library(
        library_id=model.id,
        user_id=model.user_id,
        name=LibraryName(model.name),
        basement_bookshelf_id=model.basement_bookshelf_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        soft_deleted_at=model.soft_deleted_at,
    )

def _to_orm(self, domain: Library) -> LibraryModel:
    return LibraryModel(
        id=domain.library_id,
        user_id=domain.user_id,
        name=domain.name.value,  # ValueObject unwrapping
        basement_bookshelf_id=domain.basement_bookshelf_id,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        soft_deleted_at=domain.soft_deleted_at,
    )
```

## Documentation References

- **ADR-031**: Structure Refinement - Models Migration and Application Layer Consolidation
- **HEXAGONAL_RULES.yaml**: Architecture rules (Step 2 ORM migration, Part C ORM mappings)
- **DDD_RULES.yaml**: Domain rules (RULE-001, 002, 003 with UseCase references)
- **Architecture**: Hexagonal (Ports & Adapters) + Domain-Driven Design

## Status

✅ **Phase 1 (Library Module)**: COMPLETE
⏳ **Phase 2-6 (Bookshelf, Book, Block, Tag, Media)**: Pending (same pattern to be applied)

---

*Last Updated: November 14, 2025*
*Module Status: Production-ready (pending integration testing)*
