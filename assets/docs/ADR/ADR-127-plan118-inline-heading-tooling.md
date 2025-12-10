# ADR-127 Plan118 Inline Heading Tooling

## Status

Status: Accepted
    - `frontend/src/features/block/legacy/BlockList.tsx` now renders a "正文 / H1 / H2 / H3" chip only for blocks whose local kind is `paragraph` or `heading`. The chip stays hidden until the block is hovered or focused, matching Plan118’s “document look” requirement。
    - `frontend/src/features/block/legacy/insertMenuConfig.ts` annotates heading items with `headingLevel`, and `BlockInsertOptions` gains an optional `headingLevel`. This metadata flows through inline `+`, bottom insert menus, and Slash commands so that inserting a heading produces the correct serialized content without post-processing。

## Context
- Slash commands could only insert new blocks. Converting the current block to a heading required a full save cycle or manual editing of `Block.type` and `content.level`.
- Markdown habits such as typing `## ` at the start of a line generated literal characters rather than semantic headings, causing rework and dirty diffs.

Plan118 closes these gaps while keeping the Domain schema (`type`, `content.level`, `content.text`) untouched.

## Decision

1. **Text-kind chip for paragraph/heading blocks**
   - `frontend/src/features/block/ui/BlockList.tsx` now renders a "正文 / H1 / H2 / H3" chip only for blocks whose local kind is `paragraph` or `heading`. The chip stays hidden until the block is hovered or focused, matching Plan118’s “document look” requirement.
   - Clicking the chip opens a compact menu. Selecting an option calls `onTransformBlock`, which routes through `useUpdateBlock` so only `type` and `content` change.
   - Non-textual blocks (todo_list, callout, media) never render the chip, preventing accidental coercion into unsupported kinds.

2. **Caret-driven Slash commands and Markdown shortcuts**
   - `frontend/src/features/block/legacy/BlockRenderer.tsx` upgrades `ParagraphEditor` with a Slash command catalog (`SLASH_COMMANDS`). Commands can either insert a new block or transform the current one (e.g., `/h1`, `/text`).

## Consequences

- Writers can promote or demote text without leaving the caret, aligning Wordloom’s editor with industry-standard UX expectations.
- Because the Domain contract is untouched, backend services, DTOs, and migrations require no updates; regression risk stays confined to the UI layer.
- Documentation now captures the UI/adapter responsibilities (`assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`), reducing the chance of future regressions (e.g., chips appearing on non-text blocks).
- The shared `BlockInsertOptions.headingLevel` keeps all insertion paths consistent, simplifying future tooling such as “convert selection to outline.”

## References

- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_118_BlockTypeTitle.md
- assets/docs/DDD_RULES.yaml (`plan118_inline_heading_controls`)
- assets/docs/HEXAGONAL_RULES.yaml (`plan118_text_kind_controls`)
- assets/docs/VISUAL_RULES.yaml (`block_insert_menu_plan85.text_kind_chip`, `markdown_shortcuts`)
- frontend/src/features/block/ui/BlockList.tsx
- frontend/src/features/block/legacy/BlockRenderer.tsx
- frontend/src/features/block/ui/insertMenuConfig.ts
- frontend/src/features/block/ui/BlockList.module.css
