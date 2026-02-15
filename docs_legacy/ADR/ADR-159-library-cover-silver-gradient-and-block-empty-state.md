# ADR-159 Library Cover Silver Gradient And Block Empty-State Typography

## Status

Status: Accepted
Date: 2025-12-08
Authors: Library Surface Guild

## Context

1. **Library cover fallbacks drifted from the current visual kit.** Older deterministic gradients plus the "LIBRARY COVER" overlay text looked mismatched next to the refreshed bookshelf dashboard and conflicted with screenshots captured for admin reviews.
2. **Loading placeholders regressed to blank boxes.** While the grid/list refactor shipped without regressions, the skeleton shimmer that once conveyed progress never returned, so QA videos showed content popping in with no chromatic continuity.
3. **Block editor empty-state notices screamed louder than placeholders.** `.emptyState` text used a darker tone and heavier weight than `.textBlockContent[data-empty]::before`, so users thought the editor already contained content even when every block was empty.

## Decision

1. **Adopt a single silver gradient fallback across every library surface.** `LibraryCoverAvatar` now defaults to `DEFAULT_LIBRARY_SILVER_GRADIENT`, removes any helper copy, and relies on the uppercase initial only when no cover exists, ensuring screenshots always show the polished metallic sheen.
2. **Restore shimmer skeletons for both grid and list cards.** `LibraryCardSkeleton` reintroduces the gradient-backed shimmer overlay so loading states mirror real covers and suppress layout jank.
3. **Align block empty-state typography with placeholder tokens.** `.emptyState` inherits the same `#9ca3af` color + 400 weight used by inline placeholders so the hint reads as secondary guidance rather than actual content.

## Consequences

* **Positive:** Admin library lists, cards, and avatars exhibit the same silver fallback, so documentation screenshots remain stable even without uploaded covers.
* **Positive:** The shimmer skeleton gives users an immediate sense of progress and hides late API responses without flashing stark white blocks.
* **Positive:** Block editor empty hints now fade into the chrome, making it obvious that the canvas is blank until the user types.
* **Negative:** Any feature wanting bespoke fallback colors must explicitly opt out; the shared constant will otherwise override legacy palettes.

## Implementation Notes

* `frontend/src/entities/library/components/LibraryCoverAvatar.tsx` now imports `DEFAULT_LIBRARY_SILVER_GRADIENT` and removes the temporary "LIBRARY COVER" text treatment.
* `frontend/src/features/library/ui/LibraryCardSkeleton.tsx` and `LibraryCardSkeleton.module.css` provide the shimmering placeholders that `LibraryList` renders before real data arrives.
* `frontend/src/modules/book-editor/ui/bookEditor.module.css` updates `.emptyState` / `.emptyHint` color + font weight to mirror the inline placeholder token.
* `assets/docs/VISUAL_RULES.yaml` records the silver gradient fallback, shimmer loading contract, and EMPTY-STATE-04 typography guardrail.

## References

* `frontend/src/entities/library/components/LibraryCoverAvatar.tsx`
* `frontend/src/features/library/ui/LibraryCardSkeleton.tsx`
* `frontend/src/features/library/ui/LibraryCardSkeleton.module.css`
* `frontend/src/modules/book-editor/ui/bookEditor.module.css`
* `assets/docs/VISUAL_RULES.yaml`
