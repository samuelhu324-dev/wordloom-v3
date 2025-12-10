# Book Editor Contract

Authoritative reference for mounting `BookEditorRoot` in any surface (admin books page, blocks workspace, future tools).

## Hosting requirements
- Provide a valid `bookId` (UUID) and render inside a React client boundary.
- Ensure `@tanstack/react-query` is configured globally because `BookEditorRoot` relies on `useBlocks` and `useMutation` hooks.
- Supply CSS scope via `bookEditor.module.css`. Do not wrap the editor with containers that clip `position: absolute` overlays (slash menu, inline toolbar).
- Parent layouts must reserve at least 640px width; below that, inline toolbar overflow is undefined.

## Allowed props
```
<BookEditorRoot
  bookId={book.id}
  onBlockCreated={(id) => analytics.track('block_created', { id })}
  onBlockDeleted={(id) => toast.info('Deleted block ' + id)}
/>
```
- `onBlockCreated` fires after the local insert controller finishes optimistic reconciliation and announces focus intent.
- `onBlockDeleted` mirrors server delete success (or downgrade noop) and should never mutate editor state directly.

## Integration rules
1. **Single provider** – Do not nest `BookEditorProvider` manually. `BookEditorRoot` owns it and exposes mutations through hooks in `model/` (e.g., `useBlockCommands`).
2. **Legacy components off-limits** – Imports from `@/features/block/legacy/*` are lint-blocked. New hosts must exclusively use `modules/book-editor` entry points.
3. **Command hooks** – Only call hooks exported from `model/` inside children rendered by `BookEditorProvider`. External consumers should interact via props/events rather than reaching into the store.
4. **Autosave contract** – `BlockItem` debounces mutations at 300ms. Wrappers must not unmount the editor during navigation (use suspense boundaries if data refetches are required) to avoid dropping unsaved drafts.
5. **Focus propagation** – Surrounding layouts must not intercept pointer events inside the editor; otherwise `selectionStore` cannot deliver caret intents (affects slash menu, delete fallback, todo list focus).

## Testing expectations
- Run `npm run test` after touching code inside `modules/book-editor`. The Vitest suite now includes markdown shortcut coverage and keyboard guard rails.
- Manual smoke tests per `BEHAVIOR_AUDIT.md` remain mandatory until Playwright coverage lands.

## Future extensions
- Expose a read-only mode via `BookEditorRoot` prop once viewer pages need the same rendering stack.
- Publish a small event bridge so other panels can react to `blockCommands` (e.g., timeline updates) without poking internal state.
