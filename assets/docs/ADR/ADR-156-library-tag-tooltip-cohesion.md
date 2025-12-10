# ADR-156 Plan175 Library Tag Tooltip Cohesion

## Status

Status: Accepted
Date: 2025-12-06
Authors: Library Experience Working Group (Plan175)

## Context

1. **Tag descriptions disappeared once libraries left the admin catalog.** The API powering the overview cards returned only `id`, `name`, and `color`, so curators had to reopen /admin/tags to confirm what each label meant.
2. **Browser-native tooltips clashed with our custom pills.** `title` attributes produced cramped boxes, duplicated strings, and flicker when combined with hover transforms, especially on pinned cards where overlay jitter was already an issue.
3. **The tag catalog shell itself jittered.** The table card used `transform`-based hover lifts while the control strip floated on a different baseline, so every refetch caused a visual “jump” and misaligned toggles.

## Decision

1. Extend the library tag DTOs with `description`. `ListLibraryTagsUseCase`, the repository join, and the FastAPI router all forward the optional text, and `LibraryTagSummaryDto` on the frontend now consumes the same field.
2. Move tooltip ownership into `LibraryTagsRow`. Chips with descriptions show a custom pseudo-element bubble (max 360px, ellipsis, rgba(17,24,39,0.92) background) that appears on hover/focus, exposes `aria-label="{name}：{description}"`, and adds a visually hidden span for screen readers. Chips without descriptions keep the lightweight `title` fallback. Host components such as `LibraryCard` no longer set their own `title`, preventing double-tooltips.
3. Polish the tags admin page so it matches the rest of the admin shell: controls align on a single baseline, the catalog `Card` keeps `transform: none` (hover only tweaks `box-shadow`), and the description column clamps at 360px to stop layout shifts.

## Consequences

* **Positive:** Library overviews finally surface the descriptive copy authors already maintain, reducing trips back to /admin/tags.
* **Positive:** The new tooltip is accessible (keyboard focusable, screen reader text) and visually consistent with other overlays, fixing long-description truncation and title flicker.
* **Positive:** Admin catalog cards stay pinned in place during refetches, so QA can scroll, select checkboxes, or open dialogs without the card bouncing.
* **Negative:** Because the tooltip is custom, any future theme change must update both the CSS tokens and the pseudo-element palette; forgetting to do so will cause mismatched overlays.

## Implementation Notes

* Backend: `backend/api/app/application/ports/input.py`, `output.py`, `routers/library_router.py`, `use_cases/list_library_tags.py`, and `infra/storage/library_tag_association_repository_impl.py` now read/write the `description` column.
* Frontend shared types: `frontend/src/entities/library/types.ts` includes `description?: string` on `LibraryTagSummaryDto`.
* Tooltip UI: `frontend/src/features/library/ui/LibraryTagsRow.tsx` + `.module.css` own the tooltip, focus handling, and visually hidden text.
* Host cleanup: `frontend/src/features/library/ui/LibraryCard.tsx` removes the legacy `title` attribute so only the tag chip controls the tooltip.
* Admin alignment: `frontend/src/app/admin/tags/page.tsx` & `.module.css` update the control grid, hover behavior, and description truncation.
* Documentation: `assets/docs/VISUAL_RULES.yaml` now records the tooltip + catalog guardrails.

## References

* `assets/docs/VISUAL_RULES.yaml`
* `frontend/src/features/library/ui/LibraryTagsRow.tsx`
* `frontend/src/app/admin/tags/page.module.css`
* ADR-096 (layout baseline) for related library/list guidance
