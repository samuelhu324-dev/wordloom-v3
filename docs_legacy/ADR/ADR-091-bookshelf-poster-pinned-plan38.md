# ADR-091: Bookshelf Poster Cards & Pinned Segments (Plan 38 Stage 4)

- **Status**: Accepted – November 23, 2025
- **Deciders**: Library Experience Working Group
- **Related Docs**: Plan_38_BookshelfOverhaul.md, VISUAL_RULES.yaml, HEXAGONAL_RULES.yaml, DDD_RULES.yaml, ADR-070-bookshelf-cover-and-default-library.md

## Context
- Library detail view previously reused legacy bookshelf cards (no cover control, no pinned grouping) and still depended on `{items,total}` pagination responses.
- Stage 4 of Plan 38 mandates Poster-style bookshelf cards, Pinned vs Others segmentation, toast-based guard when approaching the 100-shelf cap (RULE_004_UI_MAX_100), and migration to Pagination Contract V2.
- Cover customization remains Phase A (frontend-only) until Media association (Phase B) lands; UX guidelines require hover-only illustration buttons sharing ImageUrlDialog behavior.
- Without a formal decision record the three RULES documents cannot assert the new baseline for Bookshelf widgets, and backend teams lack clarity on pagination contract expectations.

## Decision
1. Adopt Poster-style bookshelf cards in both grid and list layouts, mirroring Library cards while embedding `bookshelf:cover:{id}` overrides and hover actions per RULE_BS_ILLUSTRATION_BUTTON.
2. Enforce Pinned segmentation entirely in the UI layer: `is_pinned` items render under a dedicated "PINNED" heading, followed by remaining shelves honoring sort/filter choices; empty segments collapse automatically.
3. Guard the 100-shelf invariant visually and behaviorally: surface `x/100` counts, show a progress bar starting at 80%, and block creation when the backend total reaches 100 using toast messaging instead of modal alerts.
4. Update the `/api/v1/bookshelves` adapter to consume and emit Pagination Contract V2 `{items,total,page,page_size,has_more}`, passing explicit `skip/limit` from the UI and logging a TODO-tagged warning when backend responses are still V1.
5. Limit cover management to frontend storage (Phase A) while documenting the dependency on ADR-070 for future Media association—no domain or repository changes occur in this stage.

## Consequences
- ✅ Visual consistency: Library detail pages now share the Poster vocabulary, making hover controls and badges predictable across aggregates.
- ✅ Clear policy reinforcement: RULE_004_UI_MAX_100 and pinned behavior are codified in VISUAL/HEXAGONAL/DDD rules, ensuring future contributors respect the guardrails.
- ✅ Pagination correctness: Metrics, list widgets, and derived data (e.g., Library KPIs) now rely on backend-provided totals/has_more instead of guessing via `items.length`.
- ⚠️ Frontend complexity increases (localStorage usage, dialog plumbing, segmented rendering) and demands regression coverage during UI tests.
- ⚠️ Backends that have not yet shipped `has_more` will trigger TODO:REMOVE-V1-COMPAT warnings until their responses are upgraded before the 2025-12-15 sunset.

## Implementation Notes
- Main components: `frontend/src/widgets/bookshelf/BookshelfMainWidget.tsx`, `frontend/src/features/bookshelf/ui/BookshelfCard.tsx`, `frontend/src/features/bookshelf/model/api.ts`, `frontend/src/features/bookshelf/model/hooks.ts`.
- Shared dialog: `ImageUrlDialog` backend-agnostic URL validation with preview.
- Toast utility replaces blocking alerts across creation guard flows.
- React Query keys now include `{libraryId,page,pageSize}` to avoid cache collisions across pagination params.
- Local storage keys: `bookshelf:cover:{bookshelfId}` for covers, `wl_bookshelves_view_<libraryId>` / `wl_bookshelves_sort_<libraryId>` / `wl_bookshelves_filter_<libraryId>` for UI state.

## Rollout & Follow-up
1. Rules sync (Stage 5): Update VISUAL_RULES (Poster + pinned), HEXAGONAL_RULES (adapter alignment), and DDD_RULES (policies for pinned/pagination) **completed**.
2. ADR-091 (this document) serves as the canonical reference for future Media association (Phase B) and Pagination V2 enforcement checkpoints.
3. Stage 6+ items: minor UI tweaks, regression testing, and eventual Media-backed cover strategy once `/media` association endpoints mature.
4. Monitoring: keep the TODO warning in place until `/bookshelves` responses consistently emit `has_more`; remove legacy fallback by 2025-12-15 as mandated in CONVENTION-RESPONSES-001.
