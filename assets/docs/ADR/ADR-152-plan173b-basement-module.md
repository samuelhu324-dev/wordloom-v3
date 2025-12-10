# ADR-152 Plan173B Basement Application Module

## Status

Status: Accepted
Date: 2025-12-05
Authors: Backend Platform Guild (Plan173B)

## Context

1. **Basement logic was scattered across legacy book use cases.** Soft-delete, restore, and hard-delete rules lived inside `DeleteBookUseCase`/`RestoreBookUseCase` with ad-hoc router glue, so Admin routes could not reuse a single dependency-injected entry point.
2. **Domain aggregates lacked provenance metadata.** `Book` could not remember which bookshelf it came from once it entered Basement, and `Block` had no `deleted_at` marker, making Paperballs/Basement/DeletedBlocksPanel flows diverge.
3. **Routers bypassed hexagonal rules.** Prior integrations issued raw SQL against `books` to list deleted items, skipping pagination contracts, DI factories, and event publishing. This also left Chronicle/QuickLog blind to Basment actions.

## Decision

1. **Create `backend/api/app/modules/basement`.** The module defines DTOs, `BasementBookSnapshot`, dedicated exceptions, and five use cases (`MoveBookToBasement`, `RestoreBookFromBasement`, `HardDeleteBook`, `ListBasementBooks`, `SoftDeleteBlock`). A FastAPI router under `/api/v1/admin` exposes the admin endpoints and relies exclusively on DI container factories.
2. **Extend domain + infra models.** `Book` now persists `previous_bookshelf_id` and `moved_to_basement_at` while gating `move_to_basement()/restore_from_basement()/mark_deleted()` invariants. `Block` gains `deleted_at`, so one Delete/Restore pipeline serves Paperballs and Basement. SQLAlchemy models, repositories, and migrations were updated accordingly.
3. **Standardize repository + event wiring.** `IBookRepository.get_deleted_books` accepts optional `book_id` filters and is the only basement listing source. DIContainerReal exposes new factory methods, and all use cases publish the existing Book events so Chronicle + QuickLog stay consistent.

## Consequences

* **Positive:** All Basement mutations flow through one module, improving testability and keeping FastAPI routers thin.
* **Positive:** Admin tooling can show the prior bookshelf and timestamp because `BasementBookSnapshot` serializes the new metadata.
* **Positive:** Block deletion semantics are identical everywhere; UI reuse of DeleteBlockUseCase stays aligned with Paperballs.
* **Negative:** Additional columns increase migration/testing surface; every create/restore path must now hydrate the new fields.
* **Negative:** DI container grows by five factories, so future maintenance must keep constructors lightweight.

## Implementation Notes

* Module scaffolding: `backend/api/app/modules/basement/{domain,application,routers}` plus DTOs/schemas/exceptions.
* Router: `basement_router.py` exposes `move-to-basement`, `restore-from-basement`, `DELETE /books/{id}`, and `GET /libraries/{id}/basement/books` endpoints.
* DI: `api/app/dependencies_real.py` now publishes `get_move_book_to_basement_use_case`, `get_restore_book_from_basement_use_case`, `get_hard_delete_book_use_case`, `get_list_basement_books_use_case`, and `get_soft_delete_block_use_case`.
* Domain/infra alignment: `book.domain.Book` + `infra/database/models/book_models.py` track previous bookshelf + timestamps; `block_models.py` plus `Block` aggregate handle `deleted_at`.
* Repository updates: `SQLAlchemyBookRepository` persists/filters the new fields, and `get_deleted_books` supports `book_id` for single-record recovery. Block repository writes/clears `deleted_at` during delete/restore.

## References

* Plan: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_173B_BasementImplementation.md`
* Rules: `assets/docs/HEXAGONAL_RULES.yaml` (module_basement section) & `assets/docs/DDD_RULES.yaml` (Plan173B policies)
* Code: `backend/api/app/modules/basement/*`, `api/app/dependencies_real.py`, `api/app/modules/book/domain/book.py`, `infra/database/models/{book,block}_models.py`
