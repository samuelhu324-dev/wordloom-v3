# ADR-144 Plan157A Cursor Intent Store

## Status

Status: Accepted
Date: 2025-12-03
Authors: Block Editor Working Group (Plan157A)

## Context

1. **Pointer clicks kept fighting programmatic caret placement.** The BlockEditorCore auto-focus effects, focusPosition props, and List/Todo inline helpers all tried to "normalize" the selection after every focus change. When users clicked inside a paragraph, the browser placed the caret instantly, but an effect soon reset it to the block start and then another effect moved it back—producing the visible sweep that triggered Plan157A.
2. **Command-only intent tokens were insufficient.** Plan146 guarded command intents, yet nothing tracked pointer/keyboard/auto flows. Downstream components guessed based on props (pendingFocusIndex, focusPosition) and frequently dispatched redundant `setSelection` calls, especially after list row edits or block auto-focus scenarios.
3. **Nested editors mutated selection directly.** ListBlock/TodoListBlock queued rAF callbacks that called `document.caretRangeFromPoint` or manually set ranges. Those helpers ignored the "single BlockEditorCore owns the DOM" rule and were impossible to lint because no unified guard existed.
4. **Domain contracts must stay oblivious.** Selection glitches tempted teams to request cursor fields on UseCases. We needed a clear, documented boundary proving the fix lives entirely inside the UI adapter so the Domain layer never learns about caret state.

## Decision

1. **Introduce a shared focus intent store.** `selectionStore` now exposes `focusIntentStore` plus `announceFocusIntent/clearFocusIntent`. Valid sources are `pointer`, `keyboard`, `command`, and `auto`, each carrying an optional `targetId` token. Only blockCommands, BlockEditorRoot/BlockList, and inline shells may write intents; ESLint `selection-command-scope` keeps every other module out.
2. **BlockEditorCore gates auto-focus by intent.** Before running autoFocus, focusPosition, or readOnly-unlock flows, the core checks the current intent. If the source is `pointer` (or the targetId mismatches) it skips `placeCaret` altogether and lets the browser selection stand. Non-pointer intents that match the block consume the token and then place the caret exactly once.
3. **Nested editors emit intent instead of touching selection.** ListBlock/TodoListBlock now set pending focus plus `announceFocusIntent('keyboard'|'auto', rowId)`. ParagraphEditor/BlockEditorCore perform the actual caret work, so all `requestAnimationFrame + setSelection` hacks disappeared. Pointer paths simply mark `pointer` intent during `onMouseDownCapture`.
4. **Command flows stay on the official chain.** Create/Delete/Transform commands emit `announceFocusIntent('command', targetBlockId)` alongside `requestSelectionEdge/Offset`. SelectionManager remains command-only, but BlockEditorCore can distinguish that source when deciding whether to move the caret after a mutation.
5. **Document the guardrails.** DDD/Hexagonal/Visual RULES received Plan157A sections describing the intent taxonomy, pointer immunity, and lint guard. Any future attempt to add cursor fields to UseCases must reference these policies.

## Consequences

* **Positive:** Pointer clicks no longer suffer the "line-start sweep" because the browser-made selection is authoritative whenever `source='pointer'`.
* **Positive:** Keyboard/auto intents retain deterministic behavior—block creation, Enter, and arrow navigation still land at start/end thanks to the shared store.
* **Positive:** Nested editors no longer manipulate global selection APIs, reducing regression risk and making linting effective.
* **Negative:** UI contributors must reason about intent tokens when adding new caret flows. Failing to set an intent now results in no caret movement instead of "lucky" behavior, so onboarding docs were updated.

## Implementation Notes

* Store: `frontend/src/modules/book-editor/model/selectionStore.ts` (focusIntentStore, announce/clear helpers, TTL for pointer intents).
* Core gating: `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` (intent checks inside autoFocus/focusPosition effects + pointer capture hook).
* Command wiring: `frontend/src/modules/book-editor/model/blockCommands.ts` (announce before requestSelectionEdge) and `frontend/src/modules/book-editor/ui/BookEditorRoot.tsx` / `ui/BlockList.tsx` for auto/keyboard intents.
* Inline editors: `frontend/src/modules/book-editor/ui/BlockItem.tsx`, `ui/ListBlock.tsx`, and `ui/TodoListBlock.tsx` now emit intents instead of forcing caret placement.
* Verification: manual smoke (click inside lists/todos/paragraphs, run keyboard navigation, create/delete blocks) plus lint enforcement to keep selection APIs centralized.

## References

* DDD_RULES: `POLICY-BLOCK-PLAN157A-CURSOR-INTENT-STORE`
* HEXAGONAL_RULES: `block_editor_plan157a_cursor_intent_store`
* VISUAL_RULES: `block_editor_cursor_stability` CURSOR-10~12
* QuickLog: `Plan_157A_BlockCursorWhizingThrough.md` (implementation log)


