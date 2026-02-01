# ADR-133 Plan137 Inline List Row Unification

## Status

Status: Accepted
Date: 2025-12-06
Authors: Wordloom Editor Team (Plan_137)

## Context

Todo blocks have benefitted from the inline shell since Plan130, but bulleted/numbered lists were still running the legacy "display vs editor" toggle. That split DOM caused baseline drift, double focus transitions, and inconsistent keyboard behaviour (Enter would jump to a new block, Backspace would leave behind empty wrappers, slash commands could not open in place). QA also reported that lists no longer lined up with the global Plan137 baseline after we tightened paragraph spacing, because the list CSS was a fork of the pre-Plan120 styles. We needed to bring lists onto the same inline row skeleton without touching the Block domain model or introducing new ports.

## Decision

1. **Shared inline row layout tokens**
   - `frontend/src/modules/book-editor/ui/bookEditor.module.css` now exposes `.inlineRow`, `.inlineMarker`, and `.inlineEditorText`. Todo checkboxes and list markers consume the same 18 px gutter, so bullets, numbers, and checkboxes sit on the same baseline defined in Plan120/126/137.
   - The legacy `.listEditor*` classes were removed; every inline row inherits typography, spacing, and placeholder styling from the paragraph shell.
2. **List rows reuse ParagraphEditor**
   - `frontend/src/modules/book-editor/ui/ListBlock.tsx` normalizes `content.items` into `string[]` and renders each row as `ParagraphEditor` + marker. Enter inserts a new row, Shift+Enter adds a soft break, Backspace deletes the row (or the entire block when it was the last empty row), and focus shuttles via `onFocusPrev/onFocusNext` so keyboard loops remain continuous.
   - Display mode mirrors the structure: the same `.inlineRow` skeleton renders bullets or tabular numbers plus either the text or the shared "写点什么…" placeholder.
3. **List plugins opt into the inline shell**
   - `frontend/src/modules/book-editor/model/blockPluginsImpl.tsx` wraps both `bulleted_list` and `numbered_list` kinds with `prefersInlineShell=true`, so BlockItem no longer flips between separate display/editor trees. Read-only mode simply flips `data-readonly` on the ParagraphEditor.
4. **Delete semantics stay on existing ports**
   - `frontend/src/modules/book-editor/ui/BlockItem.tsx` now treats lists the same way as todos when computing `hasText`. Pressing Backspace on an empty list triggers the existing DeleteBlockUseCase, avoiding any need for a "clear list" port or schema tweaks. The Block DTO remains `{items: string[]}`.

## Consequences

- **Positive:** Todos, paragraphs, and lists now share the same baseline tokens, so Plan137 spacing guarantees hold regardless of block mix.
- **Positive:** Keyboard flows are predictable—Enter/Shift+Enter/Backspace mirror todo behaviour, and ordered-list numbering no longer shifts focus because we stay in a single DOM tree.
- **Positive:** Screen readers receive a stable `role="group"` + marker text, and tabular numerals prevent layout jumps when the list crosses 9 items.
- **Negative:** Rendering each row through ParagraphEditor increases React node count for very long lists; we will monitor perf traces and consider virtualization if needed.

## Implementation Notes

- Key files: `frontend/src/modules/book-editor/ui/ListBlock.tsx`, `frontend/src/modules/book-editor/ui/bookEditor.module.css`, `frontend/src/modules/book-editor/model/blockPluginsImpl.tsx`, `frontend/src/modules/book-editor/ui/BlockItem.tsx`.
- Verify Enter/Shift+Enter/Backspace/focus loops via RTL/Playwright scenarios; run `npm run lint -- frontend/src/modules/book-editor` to ensure CSS modules stay type-safe.
- Manual QA: create bulleted + numbered lists, mix with todos/paragraphs, ensure baseline alignment and deletion parity in read/write modes.

## References

- Plan137 inline row notes (QuickLog, 2025-12-06)
- `assets/docs/HEXAGONAL_RULES.yaml` → `block_editor_plan137_inline_list_contract`
- `assets/docs/VISUAL_RULES.yaml` → `block_list_visual_rules`
- `assets/docs/DDD_RULES.yaml` → `POLICY-BLOCK-PLAN137-LIST-INLINE-SHELL`
