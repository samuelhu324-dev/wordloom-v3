# ADR-157 Plan176 Book Tooltip Parity

## Status

Status: Accepted
Date: 2025-12-07
Authors: Book Experience Working Group (Plan176)

## Context

1. **Showcase badge tooltips were clipped or unreadable.** `BookFlatCard` badges lived inside scrolling strips with `overflow: hidden`, so native `title` bubbles appeared off-screen and could not describe long labels or maturity states.
2. **Row view tags only surfaced raw names.** `BookRowCard` reused `tags_summary` (names only) and never received the richer description text that libraries maintain, so the `+N` overflow chip was opaque to curators.
3. **Tag descriptions were not available inside `BookMainWidget`.** The `ListBooksUseCase` contract intentionally excludes tooltip-only fields, and we had no canonical place to merge inline `library.tags` with the `/libraries/{id}/tags` catalog, leading to ad-hoc fetches and duplicated memoization attempts.

## Decision

1. **Establish a single `tagDescriptionsMap` in `BookMainWidget`.** The widget now merges inline `library.tags` (when provided) with a guarded `getLibraryTags` TanStack Query (`limit=200`). The query only fires if any loaded book carries tags that lack descriptions in the map, keeping payloads small while honoring DDD constraints (Book DTOs stay unchanged).
2. **Render Showcase badge tooltips via `createPortal`.** `BookFlatCard` anchors a tooltip bubble to the badge ref, renders it into `document.body`, and repositions on scroll/resize. The bubble copies the Library tooltip palette (rgba(17,24,39,0.92), max-width 360px, radius 8px, z-index 1600) and exposes `aria-label="标签：{name}｜{description}"` (or `成熟度：{label}` for maturity ribbons).
3. **Align Row view chips with Library tooltip rules.** `BookRowCard` now shares the pseudo-element bubble, `prefers-reduced-motion` guard, and keyboard focusability from `LibraryTagsRow`. The `+N` overflow chip presents `还有 {count} 个标签` and keeps a dashed border plus identical aria-label text.
4. **Document cross-rule guardrails.** VISUAL_RULES records the badge/row behaviors, DDD_RULES reiterates that tag descriptions remain a Library contract, and HEXAGONAL_RULES captures the portal + query responsibilities so future adapters cannot drift.

## Consequences

* **Positive:** Showcase badges are readable even inside tight carousels, eliminating clipped tooltips and user confusion about maturity ribbons.
* **Positive:** Row view chips finally expose the descriptive copy curators author, and the `+N` chip has a clear Mandarin message for keyboard and hover interactions.
* **Positive:** The `tagDescriptionsMap` prevents every card from making ad-hoc requests, guarding payload size and respecting the “Book DTO stays lean” rule.
* **Negative:** The portal tooltip introduces scroll/resize listeners; forgetting to clean them up would leak handlers, so tests and linting must watch for unmount hygiene.

## Implementation Notes

* Frontend aggregation: `frontend/src/widgets/book/BookMainWidget.tsx` builds `tagDescriptionsMap`, decides whether to call `useLibraryTagsQuery`, and passes the map through to Showcase + Row components.
* Showcase UI: `frontend/src/features/book/ui/BookFlatCard.tsx` & `.module.css` own the badge portal, measurement, z-index tokens, `aria-label`, and guardrails for maturity fallback copy.
* Row UI: `frontend/src/features/book/ui/BookRowCard.tsx` & `.module.css` adopt the shared tooltip tokens, force chips with descriptions to be focusable, and format the `+N` overflow message.
* Shared types/hooks: `frontend/src/entities/library/types.ts` and `frontend/src/features/library/model/hooks.ts` remain the single definition of `LibraryTagSummaryDto`, reused by the new query.
* Documentation: VISUAL_RULES, DDD_RULES, and HEXAGONAL_RULES each gained Plan176 sections; QA scripts reference ADR-157 when validating tooltip parity.

## Visual Reference

> Screenshot A — Showcase badge tooltip portal (Plan176) before/after.
> Screenshot B — Row view `+N` chip bubble with description copy.

## References

* `assets/docs/VISUAL_RULES.yaml`
* `assets/docs/DDD_RULES.yaml`
* `assets/docs/HEXAGONAL_RULES.yaml`
* `frontend/src/widgets/book/BookMainWidget.tsx`
* `frontend/src/features/book/ui/BookFlatCard.tsx`
* `frontend/src/features/book/ui/BookRowCard.tsx`
