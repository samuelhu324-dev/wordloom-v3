# ADR-146 Plan160 Slash Anchor and QuickInsert Split

## Status

Status: Accepted
Date: 2025-12-04
Authors: Block Editor Working Group (Plan160A/B)

## Context

1. **Slash menu coordinates drifted to the viewport origin.** The legacy implementation calculated DOMRect data inside `ParagraphEditor`, lost track of the editor shell offset, and regularly rendered the menu in the top-left corner when the page scrolled.
2. **Hover “+” and Slash shared a brittle portal.** Both entry points reused `QuickInsertMenu`, so caret-relative expectations mixed with fixed-position math. Contributors could not reason about which trigger owned the menu, preventing incremental fixes.
3. **Caret ownership leaked into child editors.** Paragraph editors sampled `window.getSelection()` directly, collapsed ranges, and attached global listeners just to keep the menu open. This duplicated state across dozens of block instances and risked double-cleanup bugs.
4. **IME composition and selection guards were missing.** Chinese/Japanese IME sessions fired `/` key events mid-composition, instantly erasing the candidate buffer. Selection events that landed outside the editor root also produced NaN coordinates with no visible failure mode.

## Decision

1. **Move slash positioning into the BlockEditor shell.** `BlockList` now owns `editorRootRef` and a `slashMenuState { open, x, y, blockId }`. Paragraph editors simply emit `onRequestSlashMenu(blockId)` when `/` is pressed at an empty line.
2. **Introduce `getSlashMenuAnchor(editorRoot)` as the only coordinate helper.** The helper validates that the current selection lives inside `editorRoot`, collapses non-caret ranges, and translates viewport coordinates into values relative to the shell container. Missing anchors fall back to `{16,16}` and log diagnostics.
3. **Render SlashMenu inline; keep QuickInsertMenu portal-only.** SlashMenu mounts inside `.bookEditorShell` (which is `position: relative`) and uses absolute positioning. Hover “+” plus the bottom CTA continue using the legacy portal-based QuickInsertMenu, formally disallowing shared rendering between the two systems.
4. **Add IME and listener guards.** Slash handlers bail when `event.nativeEvent.isComposing` is true, preventing interruptions during composition. BlockList attaches Escape/mousedown listeners only while the menu is open and tears them down immediately when closing.
5. **Reuse the same action dispatcher.** `handleQuickActionSelect(action, trigger)` accepts `trigger = 'slash' | 'plus'` to keep create/transform logic centralized without adding Domain ports. Slash-specific selections still strip the `/command` text before executing.

## Consequences

* **Positive:** Slash menus now appear directly under the caret, matching user expectations and preventing the top-left flicker.
* **Positive:** Adapters clearly separate caret-relative UI (SlashMenu) from viewport-fixed UI (QuickInsertMenu), simplifying future maintenance and Plan160C overflow work.
* **Positive:** Event listeners and DOMRect access are centralized, reducing duplicate cleanup code in each ParagraphEditor instance.
* **Negative:** Contributors must add new regression tests (Storybook/Playwright) for IME composition and caret fallback cases before touching slash behavior.
* **Negative:** Hover “+” can no longer be used as a quick escape hatch for slash bugs; fixes must go through the caret-anchored pipeline.

## Implementation Notes

* **Frontend shell:** `frontend/src/modules/book-editor/ui/BlockList.tsx` (or equivalent shell component) now stores `slashMenuState`, wires `editorRootRef`, listens for `onRequestSlashMenu`, and attaches Escape/mousedown guards.
* **Caret helper:** `frontend/src/modules/book-editor/model/getSlashMenuAnchor.ts` exports the pure helper with selection validation, range collapsing, and fallback logging.
* **Paragraph editors:** `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` only detects `/` when `isCaretAtEmptyLine()` and `!event.nativeEvent.isComposing`, then calls `props.onRequestSlashMenu(blockId)`.
* **Menu components:** `frontend/src/modules/book-editor/ui/SlashMenu.tsx` renders inside the editor shell and consumes `{x,y}` props; `QuickInsertMenu` remains portal-based and is explicitly scoped to hover “+” triggers.
* **Action wiring:** `handleQuickActionSelect(action, trigger)` unifies transform/insert logic so both triggers continue to call `CreateBlockUseCase` / `UpdateBlockUseCase` without new ports.

## References

* QuickLog: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_160A_BlockSlashCaret.md`
* QuickLog: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_160B_Assessment.md`
* DDD Rules: `POLICY-BLOCK-PLAN160-SLASH-ANCHOR`
* Hexagonal Rules: `block_editor_plan160_slash_anchor`
* Visual Rules: `block_editor_plan160_slash_anchor`
* Keyboard Rules: `block_keyboard_rules.structure_transformations./`
