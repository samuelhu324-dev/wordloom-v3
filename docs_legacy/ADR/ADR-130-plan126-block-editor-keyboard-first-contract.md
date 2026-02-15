# ADR-130 Plan126 Block Editor Keyboard-First Contract

## Status

Status: Accepted
Date: 2025-12-01
Authors: Wordloom Dev (Plan_126)

## Context

Plan126 followed the Plan120/121 block editor refinements but focused on the specific complaint that “every sentence carries three glowing icons on the right.” QA clips in `Plan_126_BlockUIRedeisgn.md` showed that the inline toolbar had become both noisy and far away from the caret, forcing writers to abandon the keyboard for simple flows like inserting or deleting blocks. Product therefore asked for a keyboard-first contract that keeps Create/Update/DeleteBlockUseCase untouched, while letting UI/Adapter logic own Enter/Backspace semantics and the inline toolbar presentation.

## Decision

1. **Enter + Backspace define the primary block lifecycle**
   - Pressing Enter inside headings/paragraphs calls `BlockListController.insertBlock({ kind: 'paragraph', position: 'after', fractionalIndex })` and then `CreateBlockUseCase`; the UI never asks the UseCase to "guess" the insertion point.
   - Shift+Enter inserts a soft line break within the active block; trimming or collapsing extra blank lines stays inside the editor component.
   - Backspace on an empty block merges selection locally and triggers `DeleteBlockUseCase` with the explicit block id. Multi-Backspace merges are handled in the adapter and re-persisted through `UpdateBlockContentUseCase` instead of inventing `merge_block` commands.

2. **Slash menu + Markdown prefixes stay closest to the caret**
   - `/` at the beginning of a block opens the inline command palette (headings, todo, quote, etc.) so block-type switching never depends on the right-side toolbar.
   - Markdown-style prefixes (`# `, `## `, `- [ ] `, `> ` …) convert the active block immediately, keeping the entire workflow keyboard-only.
   - Enter → `/todo` (or Markdown) becomes the canonical flow for inserting specialized blocks; mouse-only `+` buttons exist purely as backup affordances.

3. **Inline actions are reduced to the absolute minimum**
   - `BlockRenderer` only surfaces `comment`, `promote`, and `convert` inline actions; all other rarely used operations move into the overflow menu or slash menu.
   - Only the active (focused) block may reveal the full inline toolbar. Non-active blocks show at most a single subtle affordance (`+` or `⋯`) on hover, eliminating the “a street of icons” look.
   - Toolbar visibility is purely UI state (props + local hooks); DTOs / Events never gain `inline_actions_visible` or similar flags.

4. **Toolbar placement follows the text, not the right gutter**
   - The inline toolbar now sits near the first line of the active block (or in the left gutter) so pointer travel stays minimal when users do need the mouse.
   - Hover/focus transitions are capped at 150–200 ms opacity fades to keep the controls unobtrusive and prevent layout shifts.

5. **Documentation + contracts synchronized**
   - Added `block_editor_plan126_keyboard_contract` (HEXAGONAL), `block_editor_plan126_keyboard_visuals` (VISUAL), and `POLICY-BLOCK-EDITOR-PLAN126-UI-ONLY` (DDD) to lock the UI-only scope and remind contributors that Create/Update/Delete remain the only Domain commands.
   - `frontend/src/features/block/lib/keyboardMap.ts`, `BlockListController`, and `BlockRenderer` source comments now point back to this ADR so future shortcut additions stay inside the adapter layer.

## Consequences

- Writers can insert, transform, and delete blocks without leaving the caret, which dramatically reduces toolbar noise and pointer travel.
- The inline toolbar no longer floods every block; only the focused block shows actionable controls, and low-frequency actions collapse into an overflow entry.
- No backend or application-layer changes were required; Domain continues to expose the same UseCases while the UI dictates keyboard semantics.
- The RULES files and this ADR give reviewers a single source of truth when evaluating future keyboard or inline action proposals.

## References

- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_126_BlockUIRedeisgn.md
- assets/docs/VISUAL_RULES.yaml (`block_editor_plan126_keyboard_visuals`)
- assets/docs/HEXAGONAL_RULES.yaml (`block_editor_plan126_keyboard_contract`)
- assets/docs/DDD_RULES.yaml (`POLICY-BLOCK-EDITOR-PLAN126-UI-ONLY`)
- frontend/src/features/block/ui/BlockList.tsx
- frontend/src/features/block/ui/BlockRenderer.tsx
- frontend/src/features/block/lib/keyboardMap.ts
