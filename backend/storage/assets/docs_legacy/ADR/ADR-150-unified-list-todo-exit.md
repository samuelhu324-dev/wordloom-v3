# ADR-150 Unified List/Todo Exit Contract

## Status

Status: Accepted
Date: 2025-12-10
Authors: Block Editor Guild (Plan169B/170A)

## Context

1. **Double paragraphs after list/todo exit.** Backspace/Enter on an empty list or todo block used to trigger `ParagraphEditor` submit logic *and* `deleteBlockWithGuard`, producing two blank paragraphs and duplicated caret intents.
2. **Distributed ownership.** Paragraph editors, block shells, and delete guard all interpreted keyboard events independently, so fixes in one layer immediately regressed another (Plans 165E–168B).
3. **No single log or contract.** Keyboard decisions lacked structured output, making it impossible to prove who invoked guard or why a list exited. QA could not reproduce “only exit when list fully empty” without ad-hoc logging.

## Decision

1. **Centralize keyboard decisions.** `keyboardDecider.decideEnter/decideBackspace` now returns `KeyboardActionResult` covering `list_family_{insert,remove,exit}` and `todo_{insert,remove,exit}`. Paragraph editors only collect context (hasText, caretAtEdge, item state) and never decide structural actions.
2. **Block shells own exit semantics.** `ListBlock.tsx` and `TodoListBlock.tsx` consume list/todo actions via `handleKeyboardDecision`, set `handled=true`, and only call `deleteBlockWithGuard` when `allItemsEmpty` and a second exit intent arrives. Row-level editors mutate items but never invoke guard.
3. **Delete guard runs once.** `useBlockCommands.deleteBlockWithGuard` remains the sole block-level deletion entry point. When block shells mark `handled`, `BlockItem` suppresses onSubmit/onDeleteEmptyBlock so guard cannot fire twice.
4. **Document and audit.** BLOCK_RULES, HEXAGONAL_RULES, and DDD_RULES explicitly state that list/todo exits are block-shell responsibilities. QuickLog plans 165E–170A are backfilled with outcomes/tests, and ADR-150 is the snapshot for future contributors.
5. **Test & log.** Vitest suites (`ListBlock.test.tsx`, `TodoListBlock.test.tsx`, `keyboardDecider.test.ts`) assert the new contract, while DevTools log hooks (`[ENTER]/[shortcut]/[deleteGuard]`) trace every decision during QA.

## Consequences

* **Positive:** Enter/Backspace on empty lists/todos now produce a single paragraph, eliminating the double-guard regression and stabilizing caret intents.
* **Positive:** Debugging is faster—logs show which layer consumed each action, and RULES describe the single source of truth.
* **Positive:** Future block kinds can reuse the same `KeyboardActionResult`/handled contract without inventing new delete paths.
* **Negative:** Block shells carry more logic (pending exit flags, handled propagation), so contributors must touch multiple files for list/todo changes.
* **Negative:** Legacy components are frozen in `features/block/legacy/`; anyone relying on the old editor must migrate or maintain the fork manually.

## Implementation Notes

* `frontend/src/modules/book-editor/model/keyboardDecider.ts` defines list/todo contexts and their action results.
* `frontend/src/modules/book-editor/ui/ListBlock.tsx` and `TodoListBlock.tsx` manage pending exits, insert/remove actions, and delegate guard calls.
* `frontend/src/modules/book-editor/ui/BlockItem.tsx` inspects `handled`/`requestDelete` to avoid duplicate submissions.
* `frontend/src/modules/book-editor/model/useBlockCommands.ts` exposes `deleteBlockWithGuard` solely to block shells; row-level editors receive no direct access.
* Tests live in `frontend/src/modules/book-editor/ui/__tests__/ListBlock.test.tsx`, `.../TodoListBlock.test.tsx`, and `model/__tests__/keyboardDecider.test.ts`.
* Documentation: `assets/docs/BLOCK_RULES.yaml`, `HEXAGONAL_RULES.yaml`, and `DDD_RULES.yaml` now cite Plan169B/170A requirements; QuickLog plans 165E–170A include 2025-12-10 回填 sections.

## References

* QuickLog: Plan_165E_NoParaBlockRestoration → Plan_170A_BlockTwoParaBackspaceIssue (2025-12-10 回填)
* Rules: `BLOCK_RULES.yaml`, `HEXAGONAL_RULES.yaml`, `DDD_RULES.yaml` (Plan169B/170A updates)
* Tests: `ListBlock.test.tsx`, `TodoListBlock.test.tsx`, `keyboardDecider.test.ts`
