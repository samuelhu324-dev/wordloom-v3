# ADR-142 Plan155A Block Jitter Guard

## Status

Status: Accepted
Date: 2025-12-03
Authors: Block Editor Working Group (Plan155A)

## Context

1. Lists and todos were relying on raw `calc()` expressions to "borrow" spacing from the block list row-gap. When `--wl-space-block-list-before` dropped below `-1 * --wl-space-block-tight`, the effective distance between a paragraph and the following list became negative (row-gap 2px + margin -6px = -4px). Every edit forced the browser to recompute layout, so the block stack jittered.
2. Display and edit shells used different line-height tokens (`--wl-line-height-tight` vs `--wl-line-height-body`). Switching between read-only list rows and inline editors therefore changed each block's intrinsic height and produced visible shifts even when the spacing tokens were correct.
3. QA lacked a fast way to see whether the token math still satisfied the "no jitter" constraints. The spacing sandbox only showed qualitative cards (Paragraph → List → Paragraph), so reviewers had to open DevTools, inspect computed values, and redo algebra by hand.
4. Governance files did not mention the invariants explicitly, which made it hard to reject proposals that tried to fix jitter via new Domain fields (e.g., `row_gap_override`) instead of UI tokens.

## Decision

1. **Tokenized invariants.**
   - `--wl-space-block-tight` remains the sole row-gap owner (`row-gap: var(--wl-space-block-tight)` on `.blockList`).
   - Introduced `--wl-space-block-list-before-safe-min = calc(-1 * var(--wl-space-block-tight))` so every component has a named lower bound.
   - `--wl-space-block-list-before` and `--wl-space-block-list-after` must stay within the safe range, ensuring `row-gap + before ≥ 0` and `row-gap + after ≥ 0`. Components consume only these tokens; direct `calc()` expressions in selectors are forbidden.
2. **Typographic parity.** Added the semantic alias `--wl-line-height-list` (defaulting to `--wl-line-height-tight`) and wired it through `.inlineEditorText`, `.todoRow`, and `.todoInput`, guaranteeing identical line-height in display and edit states for list/todo rows.
3. **Jitter Guard instrumentation.** `/app/dev/spacing-test` now contains a "Plan155A Guardrails" card that reads the live token values and surfaces:
   - Row-gap + list-before sum (entry guard).
   - Row-gap + list-after sum (exit guard).
   - Display vs edit line-height delta.
   Each metric returns "Safe" / "Needs attention" so QA can screenshot objective evidence.
4. **Process + documentation.** DDD, Hexagonal, and Visual rulebooks gained the Plan155A policy sections describing the invariants, the token ownership, and the sandbox requirements. Any spacing PR must update the guard card screenshot alongside the usual Rhythm/Shell captures.
5. **UI-only scope.** All changes live in CSS/tokens/sandbox. Domain entities, Application ports, and API contracts remain untouched to prevent spacing concerns from leaking past the adapter layer.

## Consequences

* **Positive:** Lists/todos no longer jitter when switching between display and inline edit because both states share one line-height token and respect the row-gap bounds.
* **Positive:** Guard card provides an immediate, numeric health signal; reviewers and QA can block regressions without digging through DOM trees.
* **Positive:** Copying the invariant into all three rulebooks (plus QuickLog) makes it easy to reject future attempts to add spacing knobs to Domain models.
* **Negative:** Spacing PRs now require an extra screenshot (Guard card) and token documentation update, increasing paperwork but preventing silent regressions.

## Implementation Notes

* Tokens and selectors: `frontend/src/modules/book-editor/ui/bookEditor.module.css` (safe-min token, list/todo selectors, line-height alias wiring).
* QA surface: `frontend/src/app/dev/spacing-test/page.tsx` and `spacingTest.module.css` host the Guard card UI/logic.
* Documentation: `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml` now include the Plan155A guard sections.
* No migrations or API changes were necessary; everything compiles to CSS/TS.

## References

* QuickLog `Plan_155A_BlockShakingPrevention.md`
* `/app/dev/spacing-test` Plan155A Guardrails card
* ADR-138 Plan149 spacing reset, ADR-140 Plan153 shell alignment, ADR-141 Plan154 block rhythm hardening
