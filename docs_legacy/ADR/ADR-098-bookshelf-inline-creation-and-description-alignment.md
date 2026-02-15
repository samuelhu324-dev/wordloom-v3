# ADR-098: Bookshelf Inline Creation & Audit Dialog Description Alignment

- Status: Accepted (Nov 26, 2025)
- Deciders: Wordloom Core Team
- Context: Library detail dashboard, VISUAL_RULES, DDD_RULES, HEXAGONAL_RULES, Plan55 backlog
- Related: ADR-094 (Library Dashboard Theme Integration), ADR-095 (Compact List View), ADR-096 (Dashboard Layout V2), ADR-097 (Audit List Final Polish)

## Context

Following ADR-097 we still had two UX gaps inside the library detail page:

1. The `+ NEW BOOKSHELF` button still performed a route push to `/admin/bookshelves/new`, breaking the "manage everything inside the library context" policy and duplicating form logic.
2. The lightweight BookshelfTagEditDialog only updated name + tags. Operations needed to adjust the bookshelf description during audits, but had to leave the modal, causing inconsistent state between the dashboard list and detail editors.

These issues also left VISUAL/DDD/HEXAGONAL rule files partially outdated, risking future regressions.

## Decision

1. **Inline Creation Modal**: Reuse `LibraryForm` inside `frontend/src/app/admin/libraries/[libraryId]/page.tsx` to create bookshelves inline. The modal now collects name, optional description, and up to three tags. It calls `CreateBookshelfUseCase` with the current `library_id` plus resolved `tag_ids`, closes on success, and respects the existing 80/100 guardrail (show toast, do not open modal once capped).
2. **Audit Dialog Description Support**: Extend `BookshelfTagEditDialog` to expose an optional description textarea, trim inputs, and send `{name, description?, tagIds}` to `UpdateBookshelfUseCase`. New helper styling keeps the field directly under the name input, and toast messaging remains unchanged.
3. **Rules Synchronisation**: Update `VISUAL_RULES.yaml`, `DDD_RULES.yaml`, and `HEXAGONAL_RULES.yaml` to document the shared form modal, description editing contract, and tag-creation workflow. This locks the behaviour for future audits and aligns architecture documentation.

## Rationale

- Keeping bookshelf creation inside the library detail view preserves aggregate context, avoids duplicate pages, and leverages the proven LibraryForm validations.
- Allowing description edits during audits reduces context switching for operators and ensures bookshelf metadata stays accurate alongside tags.
- Documenting the flow prevents silent regressions and keeps the three RULES files authoritative after ADR-097.

## Scope

- Frontend: `frontend/src/app/admin/libraries/[libraryId]/page.tsx`, `frontend/src/features/bookshelf/ui/BookshelfTagEditDialog.tsx`, `frontend/src/features/bookshelf/ui/BookshelfTagEditDialog.module.css`, `frontend/src/features/bookshelf/ui/BookshelfDashboardBoard.tsx`.
- Documentation: `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`.

## Non-Goals

- Changing backend DTOs or adding new REST endpoints.
- Revisiting the bookshelf dashboard layout established in ADR-096.
- Introducing optimistic updates for creation/edit flows (still rely on refetch + toasts).

## Implementation Notes

- The inline modal shares tag creation helpers with the library dialog, resolving conflicts by calling `CreateTagUseCase` then reusing IDs.
- Modal close buttons honour loading states to prevent mid-flight cancellation.
- Description trimming ensures blank strings persist as `NULL` in the database.
- Query invalidation targets `['bookshelves']` and `['bookshelves','dashboard']` to refresh both list and dashboard data.

## Testing

- Manual: Verified creation toast, limit guard (>=100 shelves), and dashboard refresh after inline creation; confirmed description updates persist after reopening the audit dialog.
- Automated follow-up: Add React Testing Library coverage for submit success/failure branches (tracked separately).

## Rollback

Revert the frontend changes mentioned in Scope and restore the previous RULES entries. No database migrations are involved.

## References

- `frontend/src/app/admin/libraries/[libraryId]/page.tsx`
- `frontend/src/features/bookshelf/ui/BookshelfTagEditDialog.tsx`
- `frontend/src/features/bookshelf/ui/BookshelfTagEditDialog.module.css`
- `frontend/src/features/bookshelf/ui/BookshelfDashboardBoard.tsx`
- `assets/docs/VISUAL_RULES.yaml`
- `assets/docs/DDD_RULES.yaml`
- `assets/docs/HEXAGONAL_RULES.yaml`
