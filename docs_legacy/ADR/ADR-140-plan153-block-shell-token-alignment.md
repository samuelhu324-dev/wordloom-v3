# ADR-140 Plan153 Block Shell Token Alignment

## Status

Status: Accepted
Date: 2025-12-06
Authors: Block Editor Working Group (Plan153A + Plan153B)

## Context

1. Plan152 expanded the block spacing ladder, but block shells (paragraph/list/todo/quote/inline panels) still mixed legacy tokens such as `--wl-block-padding-y`, raw `px` values, and ad-hoc selectors. QA could not tell whether an oversized gap came from block-to-block rhythm or from a shell padding tweak.
2. Without a named set of shell tokens, designers could not review “Paragraph → Quote → Paragraph” vs. “Paragraph → List → Paragraph” combos without diving into DevTools. `/dev/spacing-test` also lacked a scenario that showed the interaction between shell padding and the Plan152 before/after bridge tokens.
3. Documentation only described vertical rhythm at the block spacing level. DDD/HEXAGONAL rules never said whether shell padding belongs to Domain, Application, or UI, so regressions often proposed adding `shell_padding` or `list_inner_gap` fields to Block DTOs.

## Decision

1. **Shell token naming + scope**
   * Introduce the `--wl-{domain}-{shell}-{element}-{property}` pattern and bind each block plugin to a dedicated shell variable (`--wl-block-shell-paragraph-padding-y`, `--wl-list-shell-padding-y`, `--wl-quote-shell-padding-y`, etc.). `.bookEditor_shell` keeps the only row-gap owner; shell tokens may only adjust padding inside `.blockItemMain` or the plugin container.
   * List/Todo/Quote/Tabs rely on bridge tokens (`--wl-space-list-before/after`, `--wl-space-todo-before/after`, `--wl-space-quote-before/after`) for block transitions. Shell padding cannot be used to “fake” extra rhythm.
2. **Alias control + cleanup plan**
   * `--wl-block-padding-y` and `--wl-block-padding-y-dense` become aliases to the new shell tokens. PRs must show the alias exit checklist in QuickLog before we delete the legacy names. Domain payloads and UseCases remain unaware of token names.
3. **Shell × Rhythm sandbox**
   * `/app/dev/spacing-test/page.tsx` adds the “Shell × Rhythm Matrix” card. It renders Paragraph → List → Paragraph, Paragraph → Todo → Paragraph, and Paragraph → Quote → Paragraph sequences plus token readouts so QA can confirm padding + before/after values without leaving the sandbox.
4. **Rule sync + review gate**
   * `VISUAL_RULES.yaml`, `DDD_RULES.yaml`, and `HEXAGONAL_RULES.yaml` now describe the shell-token guardrails and sandbox requirement. Spacing PRs must attach two screenshots (Paragraph→List→Paragraph and Paragraph→Quote→Paragraph) along with the token table; reviewers can block merges that skip the sandbox update.

## Consequences

* **Positive:** Engineers can adjust shell padding without touching block-to-block rhythm, because the owner layers are formally separated and visible in the sandbox.
* **Positive:** QA gains deterministic reproduction steps—the Shell × Rhythm Matrix exposes both the computed padding and the before/after bridge tokens.
* **Positive:** Documentation eliminates ambiguity about where shell metrics live; any attempt to add spacing fields to Domain contracts now violates an explicit rule.
* **Negative:** Every spacing change now requires sandbox screenshots and rule updates, increasing paperwork but preventing silent regressions.

## Implementation Notes

* CSS: `frontend/src/modules/book-editor/ui/bookEditor.module.css`, `frontend/src/features/block/ui/BlockList.module.css`, `frontend/src/features/block/ui/DeletedBlocksPanel.module.css`.
* Sandbox: `frontend/src/app/dev/spacing-test/page.tsx` + `spacingTest.module.css` (Shell × Rhythm Matrix card).
* Docs: `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml` (Plan153 sections).
* Tracking: QuickLog `Plan_153A_BlockShells.md` (execution plan) and follow-up checklist for alias removal.

## References

* ADR-138 Plan149 spacing reset
* ADR-139 Plan152 spacing rollout
* QuickLog: `Plan_153A_BlockShells.md`
