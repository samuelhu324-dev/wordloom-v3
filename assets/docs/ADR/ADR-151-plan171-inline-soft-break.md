# ADR-151 Plan171 Inline Soft Break Guardrails

## Status

Status: Accepted
Date: 2025-12-05
Authors: Block Editor Guild (Plan171A/171B)

## Context

1. **Shift+Enter shared the Enter path.** ParagraphEditor forwarded `Shift+Enter` to the same keyboardDecider branch that creates/deletes blocks, so inline soft breaks either produced new paragraphs or triggered list/todo exits.
2. **Inconsistent storage.** Some shells rendered `<br>` directly while persistence trimmed them, causing saved blocks to lose the visual soft break or serialize stray HTML.
3. **Whitespace-only rows blocked exits.** List/todo guards treated `"\n"` as real content, so pending exits never triggered even when the item was visually empty.
4. **Rules drift.** VISUAL/DDD/HEXAGONAL_RULES still referenced Plan161A helpers but never documented the new inline command requirements introduced during Plan171 experimentation.

## Decision

1. **Inline-only handling.** ParagraphEditor/List/Todo inline shells intercept `Shift+Enter` at the start of `onKeyDown`, call `insertSoftBreakAt(coreState, caretOffset)`, and immediately return so keyboardDecider/deleteBlockWithGuard never see the event.
2. **Helper-driven mutation.** `inlineText.insertSoftBreakAt` and `normalizeInlineValue` insert `\n` at the caret and ensure whitespace-only strings collapse to empty state checks shared by paragraph/list/todo blocks.
3. **Display via CSS, not HTML.** All text shells rely on `white-space: pre-wrap`; serialization strips `<br>` and persists only `\n`, keeping Domain payloads string-only.
4. **Regression proof.** Vitest suites (`inlineText`, `ListBlock`, `TodoListBlock`) assert that soft breaks stay in a single block/item and that lists composed of `\n` still count as empty. RULES updates (VISUAL/DDD/HEXAGONAL) capture the new guardrails.

## Consequences

* **Positive:** Shift+Enter now behaves identically across paragraph/list/todo editors, giving writers multi-line items without accidentally duplicating or exiting blocks.
* **Positive:** `\n` is the single source of truth for soft breaks, simplifying persistence, rendering, and telemetry.
* **Positive:** QA gains checklist coverage—if `Shift+Enter` reaches keyboardDecider, it is immediately detectable through test failures and RULES violations.
* **Negative:** Inline editors own more logic (caret math, normalization) and must stay in sync with BlockEditorCore updates, increasing coordination cost.
* **Negative:** Legacy editors that still emit `<br>` must migrate or accept that their output will be normalized to `\n`, potentially breaking bespoke styling.

## Implementation Notes

* Frontend: `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` now intercepts `Shift+Enter` and delegates to `insertSoftBreakAt` before bubbling other keys. List/todo shells reuse the same editor so no custom branches exist.
* Model helpers: `frontend/src/modules/book-editor/model/inlineText.ts` exposes `insertSoftBreakAt` plus whitespace-aware normalization shared by `ListBlock`/`TodoListBlock`.
* Tests: `frontend/src/modules/book-editor/model/__tests__/inlineText.test.ts`, `ui/__tests__/ListBlock.test.tsx`, and `ui/__tests__/TodoListBlock.test.tsx` each verify soft break insertion and empty-state handling.
* Documentation: `assets/docs/VISUAL_RULES.yaml`, `DDD_RULES.yaml`, and `HEXAGONAL_RULES.yaml` now contain Plan171A/B language covering inline handlers, data semantics, and QA expectations.
* Monitoring: QuickLog Plan_171A/171B entries cross-link this ADR so future caret/keyboard iterations know that `Shift+Enter` is off-limits to block-level commands.

## References

* Plans: `Plan_171A_BlockSoftLineBreaking.md`, `Plan_171B_Implementation.md`
* Code: `ParagraphEditor.tsx`, `inlineText.ts`, `ListBlock.tsx`, `TodoListBlock.tsx`
* Tests: `inlineText.test.ts`, `ListBlock.test.tsx`, `TodoListBlock.test.tsx`
* Rules: `VISUAL_RULES.yaml`, `DDD_RULES.yaml`, `HEXAGONAL_RULES.yaml`
