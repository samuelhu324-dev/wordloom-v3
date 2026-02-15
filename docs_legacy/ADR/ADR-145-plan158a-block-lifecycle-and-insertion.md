# ADR-145 Plan158A Block Lifecycle and Insertion

## Status

Status: Accepted
Date: 2025-12-03
Authors: Block Editor Working Group (Plan158A)

## Context

1. **The hover “+” entry point caused cognitive overload.** Plan148/149 already tightened padding, but the per-block insert button kept surfacing, flashing in and out as users moved the pointer. Writers asked for a stable, keyboard-first flow that keeps the canvas quiet unless they explicitly ask for structure changes.
2. **Documents briefly dropped to zero blocks.** Bulk deletions, redo/undo chains, or aggressive cleanup helpers occasionally removed the final block before a placeholder was restored. During that gap none of the keyboard handlers had a destination, producing broken focus traps and empty canvases.
3. **Enter handling diverged between paragraph and list editors.** Paragraphs split correctly, but lists created top-level siblings or left stray empty blocks depending on the plugin. The behavior was difficult to describe to contributors or encode in Copilot prompts.
4. **Slash commands were ungoverned.** Multiple experiments tried to re-introduce `/quote` or `/divider` via ad-hoc menus. Without a documented contract, nothing stopped the UI from slipping back to hover buttons or creating Domain-level insert ports just to bring back a visual affordance we intentionally removed.

## Decision

1. **Guarantee at least one block in every Book.** `book.blocks.length >= 1` is now a guarded invariant. When only one block remains, destructive inputs (Delete/Backspace/Cmd+A+Delete) clear its text but must not remove the block node. If other flows remove the last block, the UI immediately appends an empty paragraph block and moves the caret into it so the user always sees a writable line.
2. **Initialize and reset with a single empty paragraph.** Creating a new Book or clearing all content produces exactly one paragraph block that renders the placeholder copy "写点什么...". This placeholder lives in the UI adapter; the Domain sees a normal paragraph with empty text.
3. **Restrict top-level insertion paths.** The only supported ways to create new top-level blocks are (a) pressing Enter inside a paragraph, which splits the current block and inserts a new paragraph after it, and (b) clicking the "继续写 / 写点什么..." card rendered at the document tail, which calls the same append helper. List/todo Enter behavior stays scoped to the list plugin and never spawns top-level siblings.
4. **Remove hover “+” menus and per-block insert buttons.** No block shell may render floating insert affordances on hover. Contributors must use Enter splitting, the tail CTA, or future slash commands for insertion. ESLint `selection-command-scope` style rules can later be expanded to lint this policy if needed.
5. **Reserve slash commands without implementing them yet.** The UI continues to detect `/`-prefixed input so we can layer `/quote`, `/todo`, `/divider`, etc. later. Implementations must avoid adding Domain fields or resurrecting hover menus just to expose these commands early.
6. **Provide reducer-level helpers.** We standardize helpers that Copilot can call: `ensureAtLeastOneBlock(book)`, `insertParagraphAfter(blockId)`, `splitParagraphAtCaret(blockId, caretOffset)`, and `appendEmptyParagraphAtEnd()`. All destructive flows finish by invoking `ensureAtLeastOneBlock`, and the tail CTA calls `appendEmptyParagraphAtEnd` before focusing the new block.

## Consequences

* **Positive:** Users can erase everything yet always see a writable row, preventing “dead canvas” moments and ensuring keyboard handlers always have a block target.
* **Positive:** The canvas stays visually quiet; no hover tools appear while writing, aligning with the keyboard-first intent of Plans 147–157.
* **Positive:** Contributors and Copilot prompts can rely on the helper set, reducing bespoke reducer logic or accidental Domain coupling.
* **Negative:** Some advanced users lose the explicit per-block insert affordance; onboarding material must highlight the tail CTA and Enter-splitting pattern.
* **Negative:** Tests now need extra coverage to prove `ensureAtLeastOneBlock` fires after destructive commands and that the placeholder block appears when a Book initializes or is cleared.

## Implementation Notes

* Reducer/helpers: `frontend/src/modules/book-editor/model/blockReducer.ts`, `model/blockCommands.ts`, and `model/blockPluginsImpl.ts` gain the shared helpers plus invariant checks.
* UI shell: `frontend/src/modules/book-editor/ui/BookEditorRoot.tsx`, `ui/BlockList.tsx`, or `ui/BookEditorFooter.tsx` renders the persistent tail CTA card that calls `appendEmptyParagraphAtEnd()` and focuses the new block.
* Paragraph editor: `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` handles Enter splitting via `splitParagraphAtCaret` so the caret lands at the start of the freshly inserted block.
* List/todo plugins: `ui/ListBlock.tsx` and `ui/TodoListBlock.tsx` keep their existing intra-block Enter semantics but must not append top-level siblings; they can emit intents for `insertParagraphAfter` when exiting the list entirely.
* Validation: add unit tests around the reducer helpers plus smoke tests that delete down to one block, clear the Book, and click the tail CTA to ensure the focus stays stable.

## References

* QuickLog: `assets/docs/QuickLog/D39-52- WordloomDev/archived/Plan_158A_BlockInserts.md`
* VISUAL_RULES: `block_editor_interactions_minimal_shell` (to be appended)
* HEXAGONAL_RULES: `block_editor_plan158a_block_survivability` (to be appended)
* DDD_RULES: `POLICY-BLOCK-PLAN158A-LIFECYCLE` (to be appended)
