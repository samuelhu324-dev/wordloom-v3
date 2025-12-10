# Book Editor Behavior Audit (Dec 5, 2025)

Tracked as Plan167A follow-up to ensure the new editor shell enforces the expected authoring affordances.

## Markdown shortcuts
- Source: `ui/ParagraphEditor.tsx` delegating to `model/markdownShortcuts.ts`.
- Added shared utility plus regression tests in `model/__tests__/markdownShortcuts.test.ts` covering bullets, numbered/todo lists, and block quote promotion safeguards (caret must be at suffix of marker).
- Manual check: with a paragraph focused, type `- `, press space, shortcut transforms block via `BlockItem.handleMarkdownShortcut`.

## Slash menu invocation
- Source: `ui/ParagraphEditor` + `ui/BlockItem` hooking into `onRequestSlashMenu`, anchored via `model/getSlashMenuAnchor.ts`.
- Entry guard ensures menu only opens when caret segment empty to avoid accidental trigger mid-sentence.
- Manual scenarios to validate:
  1. Paragraph caret at start with `/` opens slash menu near caret.
  2. Typing `/` mid-line should insert literal slash (hook suppressed by `isCaretInEmptySegment`).
  3. Heading blocks inherit same menu because they share `ParagraphEditor` logic.
- Future automation: consider jsdom-based test harness for `getSlashMenuAnchor` to guarantee consistent offsets when selection collapses.

## Delete guard for special blocks
- Source: `model/blockCommands.ts` → `deleteBlockWithGuard`.
- Guard rails verified by reading through downgrade + single-block fallback logic:
  - Single base block => clears content, keeps focus.
  - Single special block => downgrades to paragraph before allowing delete.
  - Multi-block selection ensures fallback focus announced via `announceFocusIntent`.
- Manual coverage: ensure deleting last todo list downgrades to paragraph (no hard delete). Add Playwright case once dashboard harness is ready.

Summary: markdown shortcut logic now isolated + tested; slash menu and delete-guard behavior documented with manual acceptance cases pending automation.
