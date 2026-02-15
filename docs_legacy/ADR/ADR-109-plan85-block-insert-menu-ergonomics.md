# ADR-109 Plan85 Block Insert Menu Ergonomics

## Status

Status: Accepted
Date: 2025-11-27
Authors: Wordloom Dev (Plan_85)

## Context

The Blocks tab gained a rich BlockKind stack in Plan77/Plan83 (paragraph, todo_list, callout, quote, divider, image, image_gallery). The initial insert menu was implemented as a long vertical list anchored to the bottom of the page. This caused several usability issues:

- Pointer travel was large: to insert a block while reading/editing in the middle of the page, the cursor had to move to a distant bottom menu.
- The menu grew vertically as we added kinds, forming a tall column that could hit the viewport edges and force the user to "chase" the list.
- High-frequency kinds (paragraph, todo, callout, divider, image) were mixed with low-frequency kinds, making scanning and decision-making slower than necessary.

Industry-grade editors (Notion, Coda, modern document tools) typically avoid infinitely tall insert menus by:

- Capping menu height and allowing internal scrolling.
- Prioritising a small set of frequently used kinds near the cursor.
- Hiding rare kinds behind a secondary affordance ("more" or searchable palettes).

Plan85 defines how Wordloom should evolve the Block insert menu to match these patterns while keeping Domain and Ports unchanged.

## Decision

1. **High-frequency first, low-frequency in a collapsible section**

- The bottom insert menu keeps a single entry point (`+ 插入块`), but the popover groups items as:
  - **常用 (Common):** paragraph, todo_list, callout, divider (always visible).
  - **更多块类型… (More):** a toggle that expands low-frequency groups such as quote, image, image_gallery.
- The popover is capped via CSS (e.g. `max-height: 280px; overflow-y: auto;`) to ensure it never stretches from "ceiling to floor". Long lists scroll internally instead of pushing the pointer off-screen.

2. **Menu ergonomics are strictly a presentation concern**

- Domain and Application layers only accept `CreateBlockUseCase(kind, content, book_id, fractional_index)`; they are not aware of whether the block was inserted via the bottom menu, a future inline `+` handle, or a `/` command.
- No fields such as `is_frequent` or `insert_entry` are added to Block entities, DTOs, or repositories. The notion of "frequent" lives exclusively in `VISUAL_RULES.yaml` and UI components.

3. **Single insertion pipeline shared by all entry points**

- All present and future insertion affordances must flow through the same adapter:
  - UI chooses a `BlockKind`.
  - UI calls a shared createBlock hook, which wires to `CreateBlockUseCase` and serialises `createDefaultBlockContent(kind)` via `serializeBlockContent(kind, content)`.
- Variants such as an inline `+` button per block or a `/` command near the caret are allowed, but they must:
  - Call the same `onAddBlock(kind)` contract as the bottom menu.
  - Use identical default content helpers, ensuring consistent payloads and validation.

4. **Variant entry points share the same pipeline**

- **Inline `+` handles** are now live in `frontend/src/features/block/ui/BlockList.tsx`. Hovering (or focusing via keyboard) reveals `.inlineInsertRow` before/after each block, and clicking the handle opens the same grouped popover. The handler forwards `{ anchorBlockId, position, source:'inline-plus' }` to the parent page, which computes a fractional index and calls `reorderBlock` after creation.
- **Slash (`/`) commands** ship in `frontend/src/features/block/ui/BlockRenderer.tsx` (ParagraphEditor). Typing `/` opens a caret-aligned mini menu that filters `ALL_INSERT_ITEMS`, supports ↑/↓ + Enter, and removes the `/xxx` command text before inserting the new block via `onAddBlock(kind, { anchorBlockId:block.id, position:'after', source:'slash-command' })`.
- Both variants rely on the new helper `frontend/src/features/block/lib/fractionalOrder.ts` plus a shared `BlockInsertOptions` contract so every entry point flows through `CreateBlockUseCase → reorderBlock` without domain changes.

## Consequences

- Users can insert common block types with much less pointer movement, and the menu remains usable even as we add more BlockKinds.
- Inline + handles remove “scroll to the bottom” steps when inserting in the middle of a doc, and slash commands provide keyboard-first access for editors.
- Because Domain and Ports remain unchanged, backend services, tests, and Block DTOs do not need to change when menu layouts or frequenc y groupings are adjusted.
- All insert-related UX decisions are now documented in both `VISUAL_RULES.yaml` (`block_insert_menu_plan85`) and `HEXAGONAL_RULES.yaml` (`block_insert_menu_plan85_adapter`), ensuring future contributors do not re-introduce tall, ungrouped menus.
- The helper `frontend/src/features/block/lib/fractionalOrder.test.ts` (Vitest) covers fractional index computations so inline/command inserts stay deterministic.

## References

- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_85_BlockMenu.md
- assets/docs/VISUAL_RULES.yaml (`block_renderer_plan83_v2`, `block_insert_menu_plan85`)
- assets/docs/HEXAGONAL_RULES.yaml (`block_renderer_plan83_adapter`, `block_insert_menu_plan85_adapter`)
- assets/docs/DDD_RULES.yaml (`POLICY-BLOCK-PLAN77-V1-CONTENT`, `POLICY-BLOCK-PLAN83-RICH-TYPES`, `POLICY-BLOCK-PLAN85-INSERT-MENU`)
- frontend/src/features/block/ui/BlockList.tsx
- frontend/src/features/block/ui/BlockList.module.css
