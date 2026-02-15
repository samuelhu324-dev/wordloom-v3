# ADR-131 Plan128 Book Editor Plugin Registry Migration

## Status

Status: Accepted
Date: 2025-12-01
Authors: Wordloom Dev (Plan_128)

## Context

Plan128 finished the transition that started in Plan77/Plan83: the legacy `BlockRenderer` plugins (todo, callout, quote, divider, image, gallery, code, custom) were still hosted under `/admin/blocks` and Book Workspace users only saw "暂不支持的块类型" placeholders after the Plan120 inline-shell refresh. `modules/book-editor` had been handling paragraph/heading-only flows, so the new Book Editor lacked parity with the historic registry, forcing editors to jump back to the debug page for anything except plain text. Product demanded full feature parity before flipping the new editor on for all books, without adding new Domain commands or schema changes.

## Decision

1. **Single plugin registry in the new module**
   - `frontend/src/modules/book-editor/model/blockPluginsImpl.tsx` now exports the canonical registry for every supported `BlockKind` (paragraph, heading, todo_list, callout, quote, divider, image, image_gallery, code, custom).
   - Each entry wires Display + Editor components from `modules/book-editor/ui/*` and a `normalize` + `createDefaultContent` contract so BookEditorRoot can hydrate or create blocks without relying on the old renderer.
   - `getBlockPlugin` and `getRegisteredKinds` replace the ad-hoc switch statements that previously lived in `BlockRenderer`.

2. **Normalization stays UI-side but guarantees schema safety**
   - Helpers such as `normalizeTodoList`, `normalizeImageGallery`, and `normalizeCallout` coerce raw JSON into the shapes defined in `@/entities/block`, injecting scoped ids via `generateBlockScopedId()` when migrations left blank values.
   - Editors receive already-normalized payloads, emit the same structure on `onChange`, and never mutate UseCase contracts; invalid content short-circuits in the UI instead of attempting “best guess” writes.

3. **Dedicated Display/Editor components for every rich block**
   - New components (`TodoListBlock.tsx`, `CalloutBlock.tsx`, `QuoteBlock.tsx`, `DividerBlock.tsx`, `ImageBlock.tsx`, `ImageGalleryBlock.tsx`, `CodeBlock.tsx`, `CustomBlock.tsx`) live under `modules/book-editor/ui/` and share `bookEditor.module.css` tokens for todo checkboxes, gallery grids, callout pills, etc.
   - `CustomBlockDisplay/Editor` intentionally degrade to a JSON viewer/editor so historical experimental blocks remain accessible without blessing `custom` as a first-class domain aggregate.
   - `blockEditor.module.css` gained the parity styles that previously lived in the legacy renderer, keeping the visual contract centralized.

4. **Domain boundary + documentation alignment**
   - BookEditorRoot still talks to the existing hooks (`useBlocks`, `useUpdateBlock`, `useDeleteBlock`, `useBlockInsertController`); no Domain or Application contracts changed, and the legacy renderer stays around purely for QA.
   - `HEXAGONAL_RULES.yaml`, `VISUAL_RULES.yaml`, and `DDD_RULES.yaml` now capture the Plan128 responsibilities so future contributors know the registry lives entirely in the UI adapter layer.

## Consequences

- The Plan128 Book Editor can render and edit every block kind that Book DTOs emit, eliminating the “unsupported block” regression that blocked rollout.
- Plugin behavior is centralized and testable; onboarding a new block now requires adding a single registry entry plus UI components, instead of touching multiple switch statements.
- Because normalization never leaves the UI, Block UseCases keep their stable JSON contracts, and data migrations remain straightforward.
- Documentation stays in sync: reviewers can cross-reference the RULES updates and this ADR when auditing future block/editor changes.

## References

- frontend/src/modules/book-editor/model/blockPluginsImpl.tsx
- frontend/src/modules/book-editor/ui/TodoListBlock.tsx
- frontend/src/modules/book-editor/ui/CalloutBlock.tsx
- frontend/src/modules/book-editor/ui/QuoteBlock.tsx
- frontend/src/modules/book-editor/ui/DividerBlock.tsx
- frontend/src/modules/book-editor/ui/ImageBlock.tsx
- frontend/src/modules/book-editor/ui/ImageGalleryBlock.tsx
- frontend/src/modules/book-editor/ui/CodeBlock.tsx
- frontend/src/modules/book-editor/ui/CustomBlock.tsx
- frontend/src/modules/book-editor/ui/bookEditor.module.css
- assets/docs/HEXAGONAL_RULES.yaml (Plan128 updates)
- assets/docs/VISUAL_RULES.yaml (Plan128 updates)
- assets/docs/DDD_RULES.yaml (POLICY-BLOCK-EDITOR-PLAN128-PLUGIN-BOUNDARY)
