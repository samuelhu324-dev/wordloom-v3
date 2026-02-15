# ADR-132 Plan132 Heavy Block Quick Insert

## Status

Status: Accepted
Date: 2025-12-02
Authors: Wordloom Editor Team (Plan_132)

## Context

Plan130/Plan128 already stabilized the inline shell and plugin registry, but the Book Editor still behaved like a paragraph-only prototype. Power users asked for the heavier Notion-style blocks (Todo, Callout, Quote, Panel) without regressing the "one sheet of paper" flow or introducing new backend commands. Previous attempts via bottom menus created visual noise and duplicated logic between slash commands and hover "+" handles. We needed a single Quick Insert contract that could morph empty paragraphs or insert dedicated blocks, while keeping block content schemas aligned with `@/entities/block` and the existing Create/Update/Delete ports.

## Decision

1. **Unified Quick Insert action registry**
   - `frontend/src/modules/book-editor/model/quickActions.ts` declares every quick insertable kind with `{id,label,hint,kind,behavior}`. `behavior` is limited to `transform` (reuse current paragraph) or `insert-below` (always add a new block).
   - Both slash menu and hover "+" read from this registry so menu copy/order lives in one file. Adding new kinds (e.g., headings) now means updating the registry plus providing plugin support, not touching multiple components.

2. **Slash + hover "+" share the same popover**
   - `ParagraphEditor` detects `/` only when caret sits at the start of an empty paragraph, prevents default typing, and asks `BlockItem` to open the popover at the caret rect.
   - `BlockItem` mounts a minimal `+` button (`.blockAddButton`) on hover/focus, defers reveal by 150 ms, and reuses the same `QuickInsertMenu` portal.
   - The popover is a 200 px card with 12 px radius, #e5e7eb border, and a single column of label + hint buttons. ESC / outside-click closes it, and the menu never registers selection listeners outside of its open state.

3. **Transform semantics stay entirely client-side**
   - Todo/Callout/Quote act as "transform" actions when the current block is an empty paragraph. `BlockItem.transformCurrentParagraph` builds the appropriate JSON payload (checkbox id via `generateBlockScopedId`, callout variant, quote source) and replaces the paragraph by creating the new block then silently deleting the original.
   - When the paragraph already contains text—or when the user triggers the menu from the hover button—the action falls back to creating a block below the anchor, keeping existing content untouched.
   - No new backend commands exist: transforms are just `CreateBlockUseCase` + optional `DeleteBlockUseCase`, and insertions rely on `useBlockInsertController` with fractional indices.

4. **Panel becomes the first heavy-weight card block**
   - `BlockKind` now includes `panel`, mapped to API `table`. Content schema `{layout,title,body,imageUrl}` lives in `@/entities/block/types.ts` with `createDefaultBlockContent('panel')` + `ensurePanelContent` for parsing.
   - UI ships `PanelDisplay` (image placeholder + content column) and `PanelEditor` (layout select, image URL input, title/body fields) inside `bookEditor.module.css`. Layout switches between 120 px and 160 px image columns via `data-layout`.
   - Panel always uses the insert path (`behavior: 'insert-below'`), guaranteeing that the paragraph shell never tries to host a composite card.

## Consequences

- **Positive:** Slash power users and mouse-first editors now see the same lightweight UI, removing duplicated menus and reducing the chance of feature drift.
- **Positive:** Transform operations stay reversible because they are just combinations of the existing Create/Delete commands; no "changeKind" API or schema drift was introduced.
- **Positive:** Panel finally unlocks mixed media storytelling without redesigning the domain. Its schema is explicit and documented alongside other Block kinds.
- **Negative:** Transforming a paragraph into a different kind currently issues a create + delete pair, which can momentarily shift fractional indices; future optimization might inline UpdateBlockUseCase once the backend accepts cross-kind updates.

## Implementation Notes

- Key files: `ParagraphEditor.tsx`, `BlockItem.tsx`, `QuickInsertMenu.tsx`, `model/quickActions.ts`, `PanelBlock.tsx`, `bookEditor.module.css`, `@/entities/block/types.ts`.
- Tests/verification: run `npx next lint --file src/editor/undo/UndoManager.ts` (already clean) plus Storybook/Playwright scenarios for slash/hover insertions and panel editing. Hexagonal/Visual/DDD RULES now document Plan132 contracts.
- Future integration: when heading/list variants join the quick insert list, they must reuse the same registry and follow the transform-first rule for empty paragraphs.

## References

- Plan document: `assets/docs/QuickLog/D39-52- WordloomDev/archived/Plan_132_HeavierBlockTypes.md`
- Code: `frontend/src/modules/book-editor/ui/BlockItem.tsx`, `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx`, `frontend/src/modules/book-editor/model/quickActions.ts`, `frontend/src/modules/book-editor/ui/PanelBlock.tsx`
- Docs: `HEXAGONAL_RULES.yaml` (block_editor_plan132_heavy_block_contract), `VISUAL_RULES.yaml` (block_editor_plan132_heavy_block_visuals), `DDD_RULES.yaml` (POLICY-BLOCK-PLAN132-HEAVY-BLOCK-ENTRY)

> Screenshot placeholder: attach slash menu + panel card comparison after capture is ready.
