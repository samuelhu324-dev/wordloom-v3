# ADR-147 Plan161 Shift+Enter Soft Break Persistence

## Status

Status: Accepted
Date: 2025-12-04
Authors: Block Editor Working Group (Plan161A)

## Context

1. **Shift+Enter line breaks disappeared after saving.** The inline editors inserted `<br>` elements during editing, but serialization relied on `textContent.trim()` and whitespace collapsing regexes, so all soft breaks were converted into single spaces the moment a block saved.
2. **Lists and todos duplicated the issue.** Each row stored plain strings inside `{items: string[]}`; when a row contained `<br>`, the adapter would drop the tag before writing to the server, so reopening the document always showed a single line regardless of editor behavior.
3. **Display mode ignored `\n`.** Even when a newline survived, the Block renderer stuffed the raw string into a `div` with `white-space: normal`, forcing the browser to collapse every newline into a blank space and hiding the visual distinction between Enter vs Shift+Enter.
4. **Workarounds polluted the DOM.** Earlier fixes tried to inject `\n` or `<br>` manually inside keyboard handlers, which desynchronized the caret from the DOM, broke Slash-menu offsets, and reintroduced double listeners inside `ParagraphEditor`.

## Decision

1. **Normalize DOM ➜ model via a shared helper.** `extractInlineTextFromEditable` clones the contentEditable subtree, replaces every `<br>` with a text node containing `\n`, coerces `\r\n` to Unix newlines, converts `&nbsp;` to spaces, and `trimEnd`s trailing whitespace without touching interior formatting. BlockEditorCore calls this helper for paragraphs, list rows, and todos before invoking `useUpdateBlock`.
2. **Let the browser own Shift+Enter insertion.** Keyboard handlers stop `preventDefault` on `Shift+Enter`; the browser inserts `<br>`, the helper serializes it to `\n`, and `handleSoftBreak` in `BlockItem` becomes a no-op reserved for instrumentation.
3. **Render `\n` via CSS instead of manual `<br>`.** `.textBlockContent`, `.todoText`, and other Block display shells now use `white-space: pre-wrap`, so the exact serialized newline layout appears in both display and edit modes without duplicating DOM structures.
4. **Keep the Domain contract string-only.** UpdateBlockUseCase still sees `{text: string}` or `{items: string[]}`. No new fields, enums, or flags were introduced; all soft-break semantics live inside the UI adapter per DDD/Hex rules.

## Consequences

* **Positive:** Shift+Enter now survives save/refresh cycles across paragraphs, lists, and todos, matching user expectations for in-block poetry or addresses.
* **Positive:** DOM/editor parity improves because only native `<br>` nodes are created; caret math, Slash-menu anchors, and undo stacks no longer encounter phantom nodes.
* **Positive:** Rendering stays declarative (`pre-wrap`), so designers adjust typography in CSS without sprinkling `<br>` tags through React trees.
* **Negative:** QA must explicitly cover multi-line rows in regression runs; Chromatic/Playwright stories gained new snapshots, slightly increasing review noise.
* **Negative:** Any future move toward true rich text will require revisiting this helper to avoid double-escaping when spans or formatting nodes appear.

## Implementation Notes

* **Helper:** `frontend/src/modules/book-editor/model/inlineText.ts` exports `extractInlineTextFromEditable` and `normalizeInlineText`, both covered by unit tests.
* **Core wiring:** `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` invokes the helper inside `handleInput` so every plugin that reuses the core automatically inherits the behavior.
* **Keyboard behavior:** `frontend/src/modules/book-editor/model/keyboard.ts` allows the default Shift+Enter insertion, firing `onSoftBreak` solely for analytics hooks. `frontend/src/modules/book-editor/ui/BlockItem.tsx` keeps the callback but does not mutate the DOM.
* **Styling:** `frontend/src/modules/book-editor/ui/bookEditor.module.css` applies `white-space: pre-wrap` to `.textBlockContent`, `.todoText`, and `.blockDisplay` variants to keep serialized `\n` visible in read mode.

## References

* QuickLog: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_161A_BlockShiftEnterLinesIntegrationIssue.md`
* DDD Rules: `POLICY-BLOCK-PLAN161A-SOFT-BREAK`
* Hexagonal Rules: `block_editor_plan161a_soft_break_contract`
* Visual Rules: `block_editor_plan161a_soft_break_visuals`
* Keyboard Rules: `editing_and_persistence/Shift+Enter`, `list_and_todo_rows/Shift+Enter`
