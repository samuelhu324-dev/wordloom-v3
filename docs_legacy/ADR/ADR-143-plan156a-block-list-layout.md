# ADR-143 Plan156A Block List Layout

## Status

Status: Accepted
Date: 2025-12-03
Authors: Block Editor Working Group (Plan156A)

## Context

1. **List row gap depended on todo tokens.** Both list display and inline editors reused `.todoList` with `--wl-todo-item-gap`. Every attempt to tighten todo checklists also crushed bullet/numbered list rows, so designers could not tune the two independently.
2. **Bridge tokens drifted from the intended zero baseline.** After Plan155A the safe range existed, but `--wl-space-block-list-before` still surfaced as a tweakable value. A few experiments tried to push it negative again, reintroducing jitter when row-gap + before dipped below zero.
3. **No first-class exit from empty lists.** Pressing Enter on the last empty list item simply spawned more empty rows. Writers had to grab the mouse or open the Slash menu just to drop back to paragraph rhythm, which also risked leaving stray empty list blocks in the document tree.
4. **Markdown triggers covered bullets only.** Ordered lists (`1.`/`1)`) and todo syntax (`- [ ]`, `- [x]`) were ignored, so typists who rely on Markdown muscle memory still had to reach for toolbar buttons. Governance files also lacked any statement that these shortcuts stay in the UI adapter.

## Decision

1. **Lock the bridge tokens.** `--wl-space-block-list-before` is fixed at `0px` and `--wl-space-block-list-after` at `var(--wl-space-2)` (4px). Any spacing experiment must edit the tokens under Plan155A guardrails instead of patching selectors or Domain models.
2. **Give lists their own row-gap token.** Introduced `--wl-list-item-gap = var(--wl-space-2)` and a dedicated `.listBlock` class layered on top of `.todoList`, so bullet/numbered lists can diverge from todo row spacing without touching schema or UseCases.
3. **Inline exit via existing commands.** `ListEditor` now treats “last row + empty + Enter” as a command: it exits edit mode, calls `onCreateSiblingBlock` (wired to the plugin’s `onSubmit`, which already drives CreateBlockUseCase), and deletes the empty list when appropriate. No new ports or DTO fields were added.
4. **Expanded Markdown shortcuts.** `ParagraphEditor` recognizes `1.`/`1)` for numbered lists and `- [ ]`/`- [x]` for todo blocks. The shortcut handler lives entirely in the UI layer; after it fires, the paragraph text is cleared and the normal block transform pipeline runs.

## Consequences

* **Positive:** Designers can tune todo and list rhythm independently, and Paragraph ↔ List transitions stay deterministic because the bridge tokens are immutable without a Plan-level update.
* **Positive:** Writers can leave a list by pressing Enter on an empty trailing row, keeping the document free of orphaned list blocks and preserving caret intent.
* **Positive:** Markdown muscle memory now covers the common ordered/todo patterns, reducing slash-menu dependency.
* **Negative:** Spacing work now must capture two extra screenshots (Paragraph→Bulleted List→Paragraph and Paragraph→Ordered List→Paragraph) plus Guard card outputs that include `--wl-list-item-gap`.

## Implementation Notes

* Tokens and selectors: `frontend/src/modules/book-editor/ui/bookEditor.module.css` (locked bridge tokens, new `--wl-list-item-gap`, `.listBlock` gap override).
* List behavior: `frontend/src/modules/book-editor/ui/ListBlock.tsx` (Enter-on-empty exit path) and `frontend/src/modules/book-editor/model/blockPluginsImpl.tsx` (passes `onSubmit` as `onCreateSiblingBlock`).
* Markdown detection: `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` (regex updates for ordered/todo patterns).
* Documentation: `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, and `assets/docs/BLOCK_KEYBOARD_RULES.yaml` gained the Plan156A sections.

## References

* VISUAL_RULES.plan156a_list_bridge
* HEXAGONAL_RULES.block_editor_plan156a_list_bridge
* DDD_RULES.POLICY-BLOCK-PLAN156A-LIST-LAYOUT
* BLOCK_KEYBOARD_RULES (Plan156A markdown + Enter exit updates)
* Plan155A Guardrails sandbox (/app/dev/spacing-test)
