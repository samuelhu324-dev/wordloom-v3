# ADR-160 Library Title Rails And List Status Tooltips

## Status

Status: Accepted
Date: 2025-12-07
Authors: Library Surface Guild

## Context

1. **Grid card titles blended into bright photography.** The LibraryCard cover overlay relied on raw white text with no structure, so snowy or metallic covers erased the library name and made screenshots feel unfinished.
2. **List view typography fought the badge stack.** The list layout kept the name in primary text color while stacking Pinned/Archived labels above it, creating a too-bold hierarchy and no spacing cue between title and status group.
3. **Status states lacked hover/focus explanation.** Unlike the grid card badges, the list-mode "PINNED" and "ARCHIVED" pills were silent when hovered or focused, so QA could not confirm their meaning via tooltip or screen reader output.

## Decision

1. **Introduce inline rails + drop shadow for cover titles.** The cover `<h3>` inside LibraryCard now behaves like an inline-block capsule with 6px/10px padding, 1px white rules rendered via `::before/::after`, and a subtle `text-shadow: 0 1px 6px rgba(0,0,0,0.35)` so the title remains legible on luminous art.
2. **Relax list titles and attach status tooltips.** `LibraryList` keeps the name in `var(--color-text-secondary)` and wraps each `Pinned/Archived` badge with the shared `tooltipAnchor` helper, giving every badge a `data-tooltip` + `aria-label` pair that announces "已置顶书库" / "已归档书库" for hover and keyboard focus.

## Consequences

* **Positive:** Grid cards now communicate their title even on bright covers, while the dual white rails create a repeatable visual motif for hero screenshots.
* **Positive:** List view typography regains its hierarchy—the status row explains the state, and the softened title prevents visual shouting.
* **Positive:** Accessibility parity between grid and list badges eliminates QA confusion and keeps tooltip styling in a single helper.
* **Negative:** The additional pseudo-elements and shadow add a tiny rendering cost; future theme rewrites must remember to update both rails and text shadow tokens together.

## Implementation Notes

* `frontend/src/features/library/ui/LibraryCard.module.css` gained the inline-block treatment, white rails, and text-shadow on `.coverTitle`.
* `frontend/src/features/library/ui/LibraryList.tsx` now applies `tooltipAnchor` + `data-tooltip`/`aria-label` to the Pinned and Archived badges while relaxing the title tone.
* `assets/docs/VISUAL_RULES.yaml` documents the cover-title band contract plus the list status tooltip requirement.

## References

* `frontend/src/features/library/ui/LibraryCard.module.css`
* `frontend/src/features/library/ui/LibraryList.tsx`
* `assets/docs/VISUAL_RULES.yaml`
