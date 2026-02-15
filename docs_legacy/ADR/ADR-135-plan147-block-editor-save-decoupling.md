# ADR-135 Plan147 Block Editor Save/Selection Decoupling

## Status

Status: Accepted
Date: 2025-12-02
Authors: Wordloom Editor Team (Plan147)

## Context

Paragraph/heading inline editing was still inheriting the legacy autosave pipeline where every keystroke wrote through TanStack Query, refetched the entire blocks list, and re-mounted `BlockEditorCore`. Any effect that tried to "help" by re-focusing the active block would fire again after each refetch, so typing two characters often teleported the caret to the first block. In addition, several save handlers still poked `selectionStore` or DOM selections directly, meaning the cursor routinely jumped even when no refetch happened. This violated three guardrails simultaneously:

1. **DDD POLICY-BLOCK-PLAN142-AUTOSAVE-LOCAL** – only the updated block should change; no selection or structural data may piggyback on autosave.
2. **HEXAGONAL block_editor_autosave_context_contract** – BlockEditorContext must be the single source of truth; `invalidateQueries` is forbidden as a crutch.
3. **VISUAL CURSOR-01~06** – only command handlers may emit selection intents; autosave must never touch caret state.

## Decision

1. **BlockEditorCore blockId guard**
   `BlockEditorCore.tsx` now caches the last rendered `blockId` (`blockVersionRef`). When the block changes we clear any pending debounce, rewrite `textRef`, and rehydrate the DOM exactly once. While editing the same block we leave the DOM alone so the browser’s native IME/caret stays authoritative.
2. **Dedicated autosave mutation**
   All save flows call `useBlockAutosaveMutation`, which patches a single block and merges it back into `BlockEditorContext` via `upsertRenderableBlock`. React Query refetches are banned; local state reconciliation keeps DOM nodes stable.
3. **Selection intents restricted to commands**
   `selectionStore` helpers are now guarded by a custom ESLint rule (`wordloom-custom/selection-command-scope`). Only `blockCommands.ts` (create/delete/split/merge) may import `requestSelectionEdge/Offset`; autosave hooks, blur handlers, and components that merely display text can no longer compile if they touch selection APIs.
4. **Documentation + checklist**
   Plan_147 now carries a dated checklist plus Stage status markers so QA can quickly verify which safeguards shipped. DDD/HEXAGONAL/VISUAL rulesets gained matching changelog entries referencing the lint rule and the blockId guard.

## Consequences

- **Positive**: Typing triggers no DOM rewrites unless the user actually switches blocks, so IME composition and caret offsets remain stable even during rapid autosave.
- **Positive**: Any regression that tries to import `selectionStore` from a non-command module fails lint before reaching reviewers, giving us a static safety net.
- **Positive**: Observability of Plan147 improves through the checklist + rule references, making audits trivial during future cursor investigations.
- **Neutral**: Command modules must continue to request selection intents explicitly; forgetting to do so still results in caret loss, but the responsibility is now obvious and localized.
- **Negative**: Editors that legitimately need fine-grained selection control (e.g., future multi-range selections) must first extend the command layer or temporarily whitelist a new module in the lint rule.

## Implementation Notes

- Core guard: `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` (blockId + debounce reset).
- Autosave hook: `frontend/src/modules/book-editor/model/useBlockAutosaveMutation.ts`.
- Selection scope rule: `frontend/eslint-rules/selection-command-scope.js`, wired via `.eslintrc.json`.
- Context reconciliation helpers: `frontend/src/modules/book-editor/model/localBlocks.ts` and `blockCommands.ts`.
- Docs updated: `Plan_147_BlockSaveMechanism.md`, `DDD_RULES.yaml` (`POLICY-BLOCK-PLAN142-AUTOSAVE-LOCAL`), `HEXAGONAL_RULES.yaml` (`block_editor_cursor_command_policy`, `block_editor_autosave_context_contract`), `VISUAL_RULES.yaml` (`block_editor_cursor_stability`).

## References

- QuickLog: `assets/docs/QuickLog/D39-52- WordloomDev/archived/Plan_147_BlockSaveMechanism.md`
- DDD Rules: `POLICY-BLOCK-PLAN142-AUTOSAVE-LOCAL`
- Hexagonal Rules: `block_editor_cursor_command_policy`, `block_editor_autosave_context_contract`
- Visual Rules: `block_editor_cursor_stability`
- Code: `BlockEditorCore.tsx`, `useBlockAutosaveMutation.ts`, `selection-command-scope.js`
