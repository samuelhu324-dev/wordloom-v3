# ADR-138 Plan149 Spacing Token Reset

## Status

Status: Accepted
Date: 2025-12-03
Authors: Wordloom Editor Team (Plan149A + Plan149B)

## Context

Even after ADR-134, block spacing inside `modules/book-editor` drifted again because two systems kept competing:

* `.blockItem` margins defined one rhythm, but browsers kept injecting default `margin-block` on `p/ul/li/blockquote`.
* Inline shells (list/todo rows) still carried their own padding/gap and occasionally relied on `display:flex` tricks that ignored the global tokens.
* Designers had no deterministic place to verify the gaps—adjusting tokens rarely matched what the UI rendered because other layers silently overrode them.

Plan149A/B asked for a single, enforceable rule set that (1) eliminates every default margin, (2) maps the new token family to the editor shell, and (3) ships an always-on debug scene so QA can diff regressions without crafting ad‑hoc documents.

## Decision

1. **Token family reboot**
   `bookEditor.module.css` now injects `--wl-space-section`, `--wl-space-tight`, `--wl-space-inline`, `--wl-block-padding-y`, `--wl-block-padding-y-dense`, `--wl-block-padding-left`, `--wl-list-indent`, and `--wl-list-item-gap`. All block spacing selectors reference these tokens—there are no leftover hard-coded `px` values.
2. **UA margin reset lives inside `.blockItem`**
   Every descendant tag involved in textual rendering (`p`, `h1~h6`, `ul`, `ol`, `li`, `blockquote`, `.textBlockShell`, `.textBlockContent`, etc.) receives `margin-block: 0` and `padding: 0`. Quotes and other “special blocks” only use their own block-level padding knobs.
3. **Adjacency rules own tight/section logic**
   `data-kind` combinations determine whether a block inherits `--wl-space-section` or `--wl-space-tight`. Todo↔todo stacks use `--wl-space-inline` via dedicated selectors so tight chaining is provable with DevTools.
4. **Spacing Sandbox route**
   `/dev/spacing-test` (Next.js app route) renders canonical scenarios—Heading→Paragraph, Paragraph→List, Quote breaks, Todo stacks—and exposes live token values. It reuses `bookEditor.module.css`, so any regression is instantly reproducible without opening a real book.
5. **Documentation + policy sync**
   VISUAL_RULES (`block_editor_vertical_rhythm`), HEXAGONAL_RULES (`block_editor_vertical_spacing_adapter_policy`), and DDD_RULES (`POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY`) now point to this ADR, enumerate the token set, and require Sandbox screenshots in future reviews.

## Consequences

* **Positive:** Designers/QAs tweak one token and refresh `/dev/spacing-test` to validate the entire block stack; no more guessing which DOM layer owns the gap.
* **Positive:** Domain/Application layers remain oblivious to spacing knobs—UseCases continue to traffic only `kind/order/content/meta` payloads.
* **Positive:** Inline list/todo shells stay perfectly aligned because they share `--wl-space-inline` and `--wl-list-item-gap` instead of bespoke flex spacing.
* **Negative:** Every new block plugin must immediately extend the `.blockItem :is(...)` reset list; missing a tag now results in obvious regressions (and reviewers are instructed to block such PRs).

## Implementation Notes

* CSS source of truth: `frontend/src/modules/book-editor/ui/bookEditor.module.css`.
* Debug page: `frontend/src/app/dev/spacing-test/page.tsx`.
* Existing regression tests should prefer the Sandbox for screenshots; linters enforce `wordloom-custom/selection-command-scope` separately.

## References

* QuickLog: `Plan_149A_BlockSpacingManagement+.md`, `Plan_149B_Assessment.md`
* VISUAL_RULES `block_editor_vertical_rhythm`
* HEXAGONAL_RULES `block_editor_vertical_spacing_adapter_policy`
* DDD_RULES `POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY`
