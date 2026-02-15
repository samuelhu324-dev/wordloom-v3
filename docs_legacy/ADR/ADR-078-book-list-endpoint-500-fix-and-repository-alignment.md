# ADR-078: Book List Endpoint 500 Error – Repository Signature Alignment

Date: 2025-11-20
Status: Accepted
Context:
During integration testing of the bookshelf detail page, repeated 500 errors occurred on `GET /api/v1/books?bookshelf_id=...`. Frontend logging showed Axios 500 failures blocking horizontal Book Preview rendering. Inspection of backend modules revealed a mismatch between the `ListBooksUseCase` expectations and the concrete `BookRepositoryImpl` method signatures.

Problem:
`ListBooksUseCase.execute()` called:
```python
books, total = await self.repository.get_by_bookshelf_id(
    request.bookshelf_id,
    request.skip,
    request.limit,
    include_deleted=request.include_deleted
)
```
However, `BookRepositoryImpl.get_by_bookshelf_id` (and `get_by_library_id`) were defined without pagination or `include_deleted` parameters and returned only a list (not `(items, total)`). This produced a `TypeError` at runtime, triggering FastAPI's 500 response. Secondary inconsistencies: `get_by_library_id` signature mismatch, missing unified soft‑delete inclusion filtering, and duplicate `@dataclass` decorators on `BookResponse`.

Decision:
Align repository implementation with output port (`application.ports.output.BookRepository`) contract:
- Updated abstract interface in `backend/api/app/modules/book/repository.py` to include: `skip`, `limit`, `include_deleted`, and return `(List[Book], total_count)`.
- Implemented new logic for:
  - `get_by_bookshelf_id` (pagination + optional soft‑deleted inclusion)
  - `get_by_library_id` (pagination + optional soft‑deleted inclusion)
  - `get_deleted_books` (filter + pagination, returns tuple)
  - Added `exists_by_id` helper.
- Added counting queries using SQLAlchemy `func.count` for total derivation.
- Ensured filtering on `soft_deleted_at` respects `include_deleted` flag.
- Removed duplicate `@dataclass` annotation from `BookResponse`.

Rationale:
Maintaining parity between UseCase expectations and repository contracts prevents hidden runtime protocol drift. Returning `(items, total)` supports consistent pagination semantics across list endpoints (books vs bookshelves) and future UI infinite scroll or page controls. Soft‑delete inclusion flag centralizes RULE‑012 behavior and prevents ad hoc filtering in multiple layers.

Consequences:
Positive:
- Eliminates 500 TypeError on book listing.
- Provides consistent pagination + total counts for future UI enhancements.
- Centralizes deleted vs active filtering logic inside repository.
- Facilitates reuse for Basement view and unified recovery flows (RULE‑012 / RULE‑013).

Neutral / Trade‑offs:
- Slight increase in repository complexity (additional count queries). Acceptable given correctness and clarity.
- Existing code paths that consumed only lists now receive tuples; these were updated in UseCases already (ListBooksUseCase compatible). Any legacy direct repository calls must adapt if they exist.

Rejected Alternatives:
1. Patch UseCase to adapt to old repository signature (would forfeit pagination + total without fixing structural inconsistency).
2. Wrap old repository methods in an adapter layer (added indirection, delayed necessary schema convergence).

Migration / Implementation Notes:
- Patch applied to `book/repository.py` with new signatures and logic.
- Verified `ListBooksUseCase` code already expects `(items, total)`; no changes required there.
- `BookResponse` duplicate decorator removed to avoid stylistic noise (no runtime impact but cleans up code).
- Frontend should now receive a JSON shape: `{ "items": [...], "total": <int> }` from `/api/v1/books`.

Follow‑up Actions:
- Add test covering pagination and include_deleted=true scenario.
- Align deleted books endpoint to reuse the new `get_deleted_books` method internally (if not already).
- Consider consolidating duplicated repository abstractions (output port vs local abstract) to a single source of truth.
- Add UI handling for `total` when implementing page controls.

Decision Owner: Backend Integration / Data Contract Team
Approved By: Architecture Review (implicit via ADR acceptance)

Tags: pagination, repository-alignment, error-fix, RULE-012, RULE-013, data-contract
