# ADR-158 Plan175 Basement Auto Provision

## Status

Status: Accepted
Date: 2025-12-07
Authors: Basement Reliability Crew (Plan175)

## Context

1. **Library creation sometimes committed without a Basement shelf.** `libraries.basement_bookshelf_id` is non-nullable, yet `CreateLibraryUseCase` could return before `BookshelfRepository` persisted the Basement row, so concurrent move-to-basement calls crashed with FK violations and orphaned libraries.
2. **Legacy data already contained Basement shelves.** Backfills and manual repairs produced “hidden” Basement rows, but the use case always tried to insert a new one, triggering `BookshelfAlreadyExistsError` or `__init__` argument errors during retries.
3. **Frontend contracts degraded into defensive fallbacks.** Because the API occasionally returned `basement_bookshelf_id = null`, UI flows hid the Basement entry points, leaving QA unable to verify recycle-bin behaviors after creating a library.

## Decision

1. **Make Basement provisioning part of the library creation transaction.** `CreateLibraryUseCase.execute()` now calls `_ensure_basement_bookshelf()` immediately after constructing the Library aggregate, saving both entities inside the same `AsyncSession` so any failure rolls back the pair.
2. **Reuse legacy Basements before creating new rows.** `_ensure_basement_bookshelf()` queries the repository for an existing `(library_id, BASEMENT)` shelf; if present it simply returns the id and logs the reuse path, otherwise it creates `Bookshelf.create_basement(... name="Shelf")` using the ID already baked into the Library aggregate.
3. **Surface the invariant across documentation and tests.** DDD / Hexagonal / Visual rulebooks now describe Plan175A/B, and `test_library/test_application_layer_simple.py` adds a regression that seeds a legacy Basement and asserts the use case reuses it while still returning the ID to callers.

## Consequences

* **Positive:** Library creation is now atomic with Basement creation, eliminating the FK drift that previously broke move-to-basement flows and admin tooling.
* **Positive:** Frontend consumers can treat `basement_bookshelf_id` as required data, so the Basement CTA, command menus, and recovery dialogs no longer need null fallbacks.
* **Positive:** Legacy seeds and manual fixes remain valid; the new reuse path prevents duplicate Basement shelves and removes the need for ad-hoc cleanup scripts.
* **Negative:** `CreateLibraryUseCase` owns more orchestration logic, so future refactors must preserve the transaction boundary and keep `_ensure_basement_bookshelf()` aligned with repository semantics.

## Implementation Notes

* Backend use case: `backend/api/app/modules/library/application/use_cases/create_library.py` now injects both repositories, calls `_ensure_basement_bookshelf()` inside the main transaction, and handles `BookshelfAlreadyExistsError` by reusing the located shelf.
* Tests: `backend/api/app/tests/test_library/test_application_layer_simple.py` seeds `MockBookshelfRepository.existing_basements` to cover both "create" and "reuse" branches, plus asserts the response DTO exposes the persisted ID.
* Documentation: `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, and `assets/docs/VISUAL_RULES.yaml` gained Plan175A/B guardrails describing the invariant for domain, adapter, and UI layers.

## References

* `assets/docs/DDD_RULES.yaml`
* `assets/docs/HEXAGONAL_RULES.yaml`
* `assets/docs/VISUAL_RULES.yaml`
* `backend/api/app/modules/library/application/use_cases/create_library.py`
* `backend/api/app/tests/test_library/test_application_layer_simple.py`
