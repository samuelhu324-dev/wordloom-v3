# ADR-141 Plan154 Block Rhythm Hardening

## Status

Status: Accepted
Date: 2025-12-06
Authors: Block Editor Working Group (Plan154A + Plan154B)

## Context

1. After Plan152/153 we had shell tokens and bridge tokens, but spacing regressions still happened because multiple layers (bookEditorShell, blockList, individual block items) kept redefining margins, and token names were inconsistent (`--wl-space-list-before` vs raw `--wl-space-3`).
2. QA could not quickly tell whether a "Paragraph → List" bump came from the baseline row-gap or from extra margins; screenshots from `/dev/spacing-test` lacked explicit "Rhythm vs Shell" readouts and numeric guarantees.
3. Legacy aliases (`--wl-space-section`, `--wl-block-padding-y`) kept resurfacing in new diffs, and nothing enforced the "List/Todo before = 0px, after = tight" guideline. Reviewers repeatedly had to re-open PRs just to align naming and screenshot evidence.

## Decision

1. **Single rhythm owner.** `blockList` (and the editor shell that hosts it) is the only place allowed to declare block-to-block rhythm: `row-gap: var(--wl-space-block-tight)` where `--wl-space-block-tight = var(--wl-space-1) = 2px`. `.blockItem` resets `margin-block` & `padding-block` to 0 so paragraphs/headings only see the container row-gap.
2. **Token namespace.** Every inter-block distance token adopts the `--wl-space-block-*` prefix:
   * `--wl-space-block-tight`, `--wl-space-block-section`.
   * `--wl-space-block-list-before` = 0px, `--wl-space-block-list-after` = `var(--wl-space-1)` (2px).
   * `--wl-space-block-todo-before`/`after` mirror list values, quotes keep the section-level 8px tokens.
   Primitive ladder tokens (`--wl-space-0..6`, half-steps) remain the only numeric source but cannot be referenced directly by selectors.
3. **Shell confinement.** Tokens with the `--wl-*-shell-*` prefix may only appear inside `.blockItemMain` (or deeper plugin DOM) to control intra-block padding/indent. Block-level selectors can no longer multiply shell tokens to simulate rhythm. Legacy aliases `--wl-block-padding-y` / `--wl-block-padding-y-dense` stay mapped to the new shell tokens but are flagged by lint so new code cannot reintroduce them.
4. **QA & lint workflow.** Every spacing-change PR must:
   * Update `/dev/spacing-test` to show "Rhythm: --wl-space-block-… / Shell: --wl-…" labels for the edited scenario.
   * Attach screenshots for "Paragraph → List → Paragraph" and "Paragraph → Quote → Paragraph" combos.
   * Pass the lint rule that rejects deprecated token names.
   Reviewers are empowered to block merges missing either the sandbox update or the screenshots.
5. **Documentation sync.** `DDD_RULES.yaml`, `HEXAGONAL_RULES.yaml`, `VISUAL_RULES.yaml`, and QuickLog Plan154 record the above guardrails so any Domain or UseCase proposal that attempts to introduce spacing fields can be rejected immediately.

## Consequences

* **Positive:** Vertical rhythm now has one authoritative owner, so adjusting paragraph stacks or list bridges is as simple as editing a single token and verifying the sandbox readout.
* **Positive:** Designers and QA receive deterministic numbers (before = 0px, after = 2px) and no longer need to inspect DOM trees to understand spacing anomalies.
* **Positive:** Lint + screenshot gates stop legacy token names from creeping back and keep spacing discussions out of Domain/UseCase contracts.
* **Negative:** Spacing tweaks demand more paperwork (sandbox labels + two screenshots), but this is the only way to keep visual and documentation parity.

## Implementation Notes

* CSS: `frontend/src/modules/book-editor/ui/bookEditor.module.css` (row-gap owner, token namespace aliases) plus any BlockList/DeletedBlocksPanel stylesheet sharing the same tokens.
* Sandbox: `/app/dev/spacing-test/page.tsx` now prints "Rhythm" vs "Shell" for each combo so QA can compare against real documents.
* Tooling: ESLint/Stylelint rule lists `--wl-block-padding-y`, `--wl-block-padding-y-dense`, `--wl-space-section`, `--wl-space-inline`, etc., as forbidden in new diffs.
* Docs: `Plan_154A_BlockTokensNaming.md`, `Plan_154B_Assessment.md`, `DDD_RULES.yaml`, `HEXAGONAL_RULES.yaml`, `VISUAL_RULES.yaml` capture the naming grammar, numeric defaults, and QA SOP.

## References

* QuickLog `Plan_154A_BlockTokensNaming.md`
* QuickLog `Plan_154B_Assessment.md`
* ADR-138 Plan149 spacing reset, ADR-140 Plan153 shell alignment
* `/dev/spacing-test` Shell × Rhythm Matrix
