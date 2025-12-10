# ADR-153 Plan173E–H Basement Bridge & Dashboard

## Status

Status: Accepted
Date: 2025-12-06
Authors: Basement Strike Team (Plan173E–H)

## Context

1. **Delete workflows skipped the Basement module.** `DeleteBookUseCase` still contained an inline implementation of `book.move_to_basement(...)`, and the Bookshelf UI called a legacy `useDeleteBook` mutation that bypassed `/admin/books/{id}/move-to-basement`. This made the new basement router optional instead of mandatory and regularly left snapshots unsynchronized.
2. **Libraries and snapshots drifted out of compliance.** Older libraries lacked a dedicated `Bookshelf(type=BASEMENT)`, and many soft-deleted rows missed `previous_bookshelf_id`, so the UI could not show source shelves. Without a documented remediation path, QA could not trust Plan173 data until someone hand-wrote SQL fixes.
3. **Basement view lacked a consistent UX.** Prior designs rendered a flat table without hero stats, bookshelf context, or restore affordances. The new data contract (`BasementBookSnapshot`) existed but no front-end consumed it, leaving Admins to guess which shelf a book originated from.

## Decision

1. **Inject `BookBasementBridge` everywhere `DeleteBookUseCase` runs.** `backend/api/app/modules/book/application/services/basement_bridge.py` wraps `MoveBookToBasementUseCase` / `RestoreBookFromBasementUseCase`, and `dependencies_real.py` now always passes an instance into Delete/Restore book use cases. The bridge runs only after `_validate_basement_target` confirms same-library + `BookshelfType.BASEMENT` and raises `BookOperationError` when DI wiring is missing. Front-end delete buttons were rewired to `useMoveBookToBasement`, so every mutation hits `/admin/books/{id}/move-to-basement` and invalidates `['basement']` + bookshelf dashboards.
2. **Ship auditable remediation scripts.** `backend/scripts/inspect_basement_entries.py`, `backfill_basement_entries.py`, and `backfill_library_basements.py` became the only sanctioned tools for verifying/repairing missing basement shelves or snapshot rows. CI + manual rollout checklists now require running the inspectors before enabling the refreshed Basement UI; any script failure blocks deployment until data is fixed.
3. **Deliver `BasementMainWidget` with snapshot-driven UX.** `frontend/src/features/basement/api/index.ts` combines `/admin/libraries/{id}/basement/books` with `listBookshelves` to build grouped cards, hero stats, and `availableBookshelves` options. `frontend/src/widgets/basement/BasementMainWidget.tsx` renders the two-column layout, surface stats (book total, group total, lost shelves, latest deletion), enforces orphan-card theming, and drives `RestoreBookModal` so Admins can restore into the original shelf or pick another. Console diagnostics and TanStack Query safeguards (staleTime=60s, retry≤2 for 429/5xx) were added to keep QA observable.

## Consequences

* **Positive:** Delete flows are now forced through the Basement module, so every soft delete emits the same events and `BasementBookSnapshot` stays up to date across Admin/API/UI.
* **Positive:** Repeatable scripts guard against historical drift; onboarding a new environment only requires running the inspectors instead of manual SQL.
* **Positive:** The Basement dashboard finally matches the rest of the Admin experience with hero stats, grouped cards, and restore affordances fed by a single DTO.
* **Negative:** Delete operations now depend on both the Book and Basement DI graphs; misconfigured containers fail fast instead of silently deleting.
* **Negative:** BasementMainWidget performs two parallel queries (snapshots + bookshelves) and keeps cache windows short, which increases API load until pagination/backfill policies are further optimized.

## Implementation Notes

* Backend bridge + DI: `backend/api/app/modules/book/application/services/basement_bridge.py`, `.../use_cases/delete_book.py`, and `backend/api/app/dependencies_real.py` now coordinate delete/restore flows exclusively via Basement use cases.
* Front-end hook + UI: `frontend/src/features/book/model/hooks.ts` exports `useMoveBookToBasement`, and `frontend/src/widgets/book/BookMainWidget.tsx` calls it with `library.basement_bookshelf_id`, showing confirm/toast guards when the id is missing.
* Data remediation: scripts live in `backend/scripts/{inspect_basement_entries,backfill_basement_entries,backfill_library_basements}.py` and are referenced by RULES + QuickLog checklists.
* Basement dashboard: `frontend/src/features/basement/api/index.ts`, `frontend/src/features/basement/hooks/useBasementGroups.ts`, and `frontend/src/widgets/basement/BasementMainWidget.tsx` implement the new DTO contract, hero stats, and restore modal plumbing.
* Tests: `frontend/src/features/book/model/useMoveBookToBasement.test.ts` covers the hook, while backend API tests exercise the delete guard/bridge to ensure cross-library attempts return 422.

## References

* Plans: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_173E_BasementWiring.md`, `Plan_173F_BasementWiring+.md`, `Plan_173G_BasementView.md`, `Plan_173H_BasementViewImplementation.md`
* Rules: `assets/docs/DDD_RULES.yaml` (POLICY-BASEMENT-PLAN173E/F/H) & `assets/docs/HEXAGONAL_RULES.yaml` (Plan173E/F/H sections), `assets/docs/VISUAL_RULES.yaml` (Basement visual rules)
* Code: `backend/api/app/modules/book/application/services/basement_bridge.py`, `backend/api/app/modules/book/application/use_cases/delete_book.py`, `backend/scripts/inspect_basement_entries.py`, `frontend/src/features/basement/api/index.ts`, `frontend/src/widgets/basement/BasementMainWidget.tsx`
