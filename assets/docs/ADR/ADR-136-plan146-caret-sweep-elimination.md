# ADR-136 Plan146 Caret Sweep Elimination

## Status

Status: Accepted
Date: 2025-12-02
Authors: Wordloom Editor Team (Plan146)

## Context

BlockEditor inline shells finally stopped re-rendering on every autosave (Plan147), but users still saw the cursor "sweep" from the start of each block to their click target. The root causes surfaced during Plan146 quick-log analysis:

1. `selectionStore` broadcast every pending intent regardless of origin. When blocks re-rendered after structural commands, SelectionManager reapplied the last stored range even if the user manually clicked elsewhere.
2. Caret placement still followed the legacy two-step approach (`setStart(...,0)` → `setEnd(..., offset)` → `collapse(true)`), so every command request flashed a highlighted region before collapsing.
3. Click handlers on the block wrapper eagerly called `focusBlockAtStart`, overriding the browser's own caret calculation and forcing another selection replay.

The combination made every interaction look like a left-to-right sweep even though Domain contracts never asked for cursor state. We needed a single-source-of-truth rule set that kept selection exclusively in the UI adapter while letting the browser honor direct clicks.

## Decision

1. **Command-only selection intents**
   `selectionStore` intents now include `source: 'command'` tokens. Only structural commands (`blockCommands.ts`) may emit them, and SelectionManager consumes the token immediately after a caret is successfully applied. User-driven clicks do not write to the store, so browser selections remain untouched.
2. **Idempotent SelectionManager loop**
   The SelectionManager resolves every intent to a concrete offset (edge → 0/length, offset → clamped) and checks `BlockEditorCore.getCaretOffset()` before mutating the DOM. If the caret already sits at the target, the manager simply consumes the token; otherwise it calls `setCaretOffset` with an at-most five frame retry window. This removes the double-application that produced sweep animations.
3. **Single-step collapsed range setter**
   `BlockEditorCore.setCaretOffset` now walks real text nodes, creates a fallback empty text node when content is empty, clamps offsets, and executes a one-step `range.setStart(node, offset); range.collapse(true)` placement. No more intermediate "select 0..offset" segments exist, so the DOM never renders a transient highlight.
4. **Wrapper click guard + caret-from-point helper**
   `BlockItem` intercepts `mousedown` only when the target is outside the inner `contentEditable`. In such cases it uses a shared `focusCaretFromPoint` helper (preferring `caretRangeFromPoint`, falling back to `caretPositionFromPoint`) to place the caret exactly where the mouse landed. Standard clicks bubble through untouched, eliminating extraneous `focusAtEdge` calls.

## Consequences

- **Positive**: User clicks now leave the cursor exactly where the browser placed it—no visible sweep animation even when structural commands fire immediately afterward.
- **Positive**: Selection intents cannot leak outside the command layer; lint already prevented rogue imports, and now runtime tokens expire as soon as they are applied, shrinking the blast radius of bugs.
- **Positive**: The BlockEditorCore range setter doubles as the single source of truth for caret offsets, enabling future features (e.g., multi-range selections) without rewriting every command.
- **Neutral**: Command authors must keep emitting selection intents after structural mutations; forgetting to do so still results in missing carets, but the failure is scoped to the command at fault.
- **Negative**: The helper currently inserts an empty text node when a block has no text content. This is acceptable for inline blocks but requires periodic audits so richer widgets do not accumulate stray nodes.

## Implementation Notes

- `frontend/src/modules/book-editor/model/selectionStore.ts` — adds intent clamping, `getCaretOffset` checks, and strict command-only consumption.
- `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` — rewrites `setCaretOffset` to walk text nodes, create fallback nodes, and collapse in a single step while exposing `getCaretOffset` via the registry.
- `frontend/src/modules/book-editor/ui/BlockItem.tsx` — ensures `focusCaretFromPoint` only runs when clicking shell whitespace and never stomps the browser's own selection for standard text clicks.
- `frontend/eslint-rules/selection-command-scope.js` — unchanged but still enforces compile-time guardrails ensuring only command modules touch the store.

## References

- QuickLog: `assets/docs/QuickLog/D39-52- WordloomDev/archived/Plan_146A_BlockCursorSweepingThrough.md`, `Plan_146B_Assessment.md`
- Rules: `assets/docs/DDD_RULES.yaml` (`POLICY-BLOCK-PLAN146-CURSOR-INTENT-GUARD`), `assets/docs/HEXAGONAL_RULES.yaml` (`block_editor_plan146_caret_contract`), `assets/docs/VISUAL_RULES.yaml` (`block_editor_cursor_stability` CURSOR-07~09)
- Code: `selectionStore.ts`, `BlockEditorCore.tsx`, `BlockItem.tsx`
