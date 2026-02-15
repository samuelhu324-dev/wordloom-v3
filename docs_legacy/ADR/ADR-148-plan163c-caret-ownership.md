# ADR-148 Plan163C Caret Ownership Enforcement

## Status

Status: Accepted
Date: 2025-12-04
Authors: Block Editor Working Group (Plan163C)

## Context

1. **Caret "sweep" persisted even after Plan163A/B.** Pointer clicks still triggered `selectionStore.requestSelectionEdge` or `BlockItem.focusCaretFromPoint`, so the browser would place the caret on the clicked row, then legacy code rewound it to the block head before fast-forwarding back, producing a visible flash.
2. **Two competing caret sources.** The focus intent store (keyboard path) coexisted with ad-hoc `window.getSelection().set*` calls (legacy path). Because both could fire on the same render, pointer and keyboard owners continually overrode one another.
3. **SelectionStore mixed responsibilities.** It simultaneously recorded DOM selections and mutated them, so even after migrating block commands to intents, any consumer that called `requestSelectionEdge/Offset` reintroduced DOM writes outside BlockEditorCore.
4. **Documentation + lint gaps.** RULES still referenced the legacy API, and the custom ESLint guard only blocked `requestSelectionEdge` imports but did not prevent `selectionStore` reads from UI code that required them (BlockEditorCore, pointer tracking).

## Decision

1. **SelectionStore becomes read-only.** The store now exposes only `selectionStore.getSnapshot/subscribe` plus `reportSelectionSnapshot`. All `requestSelectionEdge/Offset` helpers and `useSelectionManager` were removed. Pointer and keyboard mutations must happen elsewhere.
2. **BlockEditorCore owns caret placement and telemetry.** The core watches `selectionchange` and `handleInput` to publish `{blockId, offset, textLength}` snapshots, clears the snapshot on blur/unmount, and exposes a new `focusFromPoint(x,y)` handle so callers never touch the DOM selection API.
3. **Unified intent consumption.** BlockEditorCore subscribes to `focusIntentStore`; keyboard/initial intents targeted at the block focus the editor and apply payloads (`edge` or `offset`) via a single `applyIntentPayload` helper, then immediately `clearFocusIntent(intent.token)`.
4. **Pointer flow hands off to the browser.** `BlockItem` no longer synthesizes selections. Pointer handlers announce `kind:'pointer'` intents and call `getBlockEditorHandle(blockId)?.focusFromPoint()` after edit mode is ready. The browser remains the single source of truth for pointer selections.
5. **Block commands carry caret payloads.** `createBlock` and delete fallbacks now call `announceFocusIntent('keyboard', targetId, {payload:{edge}})` with no direct selection writes. `BlockList` mirrors this when navigating between blocks so BlockEditorCore can honor user-requested edges.
6. **Lint + RULES updated.** `selection-command-scope` allows full-store imports only inside `BlockEditorCore` (read-only). New RULE entries document "Caret ownership (Plan163C)" with explicit pointer vs keyboard law, and ADR-148 links back to DDD/Hexagonal/Visual rule IDs.

## Consequences

* **Positive:** Pointer clicks never sweep through the top row because no code rewrites selections after the browser. Keyboard commands consistently land on the provided edge/offset, and intents are consumed exactly once.
* **Positive:** Selection snapshots are globally available for undo managers, diagnostics, or future slash-menu positioning without reintroducing DOM writes outside BlockEditorCore.
* **Positive:** Lint + RULES make future violations obvious. Any attempt to import `selectionStore` from UI code now fails unless the file is explicitly whitelisted, and RULES spell out the pointer/keyboard split.
* **Negative:** Consumers that previously relied on `requestSelectionEdge` (e.g., experimental QA scripts) must migrate to focus intents. The lint rule intentionally breaks those call sites.
* **Negative:** Selection snapshots are refreshed on every `selectionchange`, which may fire frequently. The implementation clamps computations to the active block and uses `requestAnimationFrame`, but QA should watch for regressions on extremely long documents.

## Implementation Notes

* **Core:** `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` owns `placeCaretAtOffset`, `focusFromPoint`, snapshot publishing, intent subscription, and blur cleanup.
* **Block shell:** `frontend/src/modules/book-editor/ui/BlockItem.tsx` only toggles edit mode, announces pointer intents, and delegates pointer placement via `focusFromPoint`.
* **Commands:** `frontend/src/modules/book-editor/model/blockCommands.ts` attaches keyboard intent payloads when creating blocks or picking selection fallbacks; `BlockList.tsx` mirrors this for inter-block navigation.
* **Store:** `frontend/src/modules/book-editor/model/selectionStore.ts` exposes only snapshot getters/subscribers and intent helpers. `useSelectionManager` and mutation APIs were deleted.
* **Lint:** `frontend/eslint-rules/selection-command-scope.js` now whitelists `BlockEditorCore` as the only UI file allowed to import `selectionStore` directly.

## References

* DDD Rules: `POLICY-BLOCK-PLAN163C-CARET-OWNERSHIP`
* Hexagonal Rules: `block_editor_plan163c_intent_contract`
* Visual Rules: `block_editor_plan163c_pointer_keyboard_split`
* QuickLog: `Plan_163A_BlockCursorWhizingThrough+.md`, `Plan_163B_Assessment.md`, `Plan_163C_Complementations.md`
