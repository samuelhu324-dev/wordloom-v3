# ADR-137 Plan148 Placeholder Overlay & Empty-State Contract

## Status

Status: Accepted
Date: 2025-12-02
Authors: Wordloom Editor Team (Plan148)

## Context

Inline blocks relied on literal placeholder text ("写点什么…") injected into the `contentEditable` so users could see where to type. Browsers therefore treated the placeholder as real content: the caret always landed after the trailing dot, selection sweeps reappeared, and autosave occasionally flushed the placeholder string to the backend. At the same time, BlockList only surfaced its hero empty-state when `blocks.length === 0`, so a freshly created book that already contained a few empty paragraphs looked like a blank piece of paper with no guidance, even though every block was technically empty.

We needed a visual-only placeholder that never polluted Block content and a deterministic way to declare “this book is actually empty” without adding new Domain fields.

## Decision

1. **BlockEditorCore owns data-empty** — the core editor now tracks emptiness per keystroke (`isTextEffectivelyEmpty`) and exposes the state via `data-empty`. Higher-level components (ParagraphEditor, List/Todo editors) no longer pass ad-hoc `data-empty` props, guaranteeing a single source of truth.
2. **Placeholder rendered as overlay** — `.textBlockContent[data-empty="true"]::before` draws the placeholder string with `pointer-events:none`, `user-select:none`, and `white-space:pre-wrap`. No placeholder characters ever enter the DOM text nodes, so caret placement and autosave operate on real content only.
3. **UI-only empty detection** — a shared helper `isRenderableBlockEmpty(block)` inspects Block DTO content on the client. BlockList considers the book “truly empty” when `blocks.length === 0` or `blocks.every(isRenderableBlockEmpty)`, and shows the onboarding card in both cases (only the zero-block case embeds `InlineCreateBar` inside the card).
4. **No Domain/API changes** — placeholder and empty-state logic stays inside the UI adapter. Neither Block DTO nor Block UseCases gain `is_empty` flags, and UpdateBlockUseCase still handles pure `{content}` payloads.

## Consequences

- **Positive**: Caret placement honors the browser’s default behavior because there is no fake text to navigate; typing over the placeholder feels instantaneous and sweep-free.
- **Positive**: Autosave payloads remain clean JSON (`{text:""}` etc.). QA can reject any occurrence of placeholder strings server-side because BlockEditorCore is the only component allowed to control `data-empty`.
- **Positive**: New users always see the onboarding card even if the bootstrap script created a few empty blocks, reducing “white page” confusion without deleting their draft structure.
- **Neutral**: BlockList now performs a lightweight client-side check over every block to decide whether to show the hero state. The helper is synchronous and works on already-loaded DTOs, so no extra network traffic occurs.
- **Negative**: Because placeholder rendering depends on CSS absolute positioning, future theme changes must keep `.textBlockContent` relative positioning intact; otherwise the overlay could drift.

## Implementation Notes

- `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` — tracks `isEmpty` state, updates it on every input, and publishes `data-empty`.
- `frontend/src/modules/book-editor/ui/bookEditor.module.css` — styles the overlay placeholder with `pointer-events:none`, `user-select:none`, and `position:absolute`.
- `frontend/src/modules/book-editor/ui/ParagraphEditor.tsx` — deletes the manual `data-empty` prop so BlockEditorCore is the lone authority.
- `frontend/src/modules/book-editor/model/isRenderableBlockEmpty.ts` — helper that inspects paragraph/heading/list/todo/callout/quote/code/panel content for meaningful text.
- `frontend/src/modules/book-editor/ui/BlockList.tsx` — shows the hero empty-state when every block is empty and reuses the helper to avoid duplicating heuristics.

## References

- QuickLog: `assets/docs/QuickLog/D39-52- WordloomDev/archived/Plan_148A_BlockAboutWritingSomething.md`, `Plan_148B_Assessment.md`
- Rules: `DDD_RULES.yaml` (`POLICY-BLOCK-PLAN148-PLACEHOLDER-EMPTY-STATE`), `HEXAGONAL_RULES.yaml` (`block_editor_plan148_placeholder_contract`), `VISUAL_RULES.yaml` (`block_editor_plan148_placeholder_visuals`)
- Code: `BlockEditorCore.tsx`, `bookEditor.module.css`, `ParagraphEditor.tsx`, `model/isRenderableBlockEmpty.ts`, `BlockList.tsx`
