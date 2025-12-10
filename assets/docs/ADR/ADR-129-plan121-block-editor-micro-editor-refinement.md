# ADR-129 Plan121 Block Editor Micro Editor Refinement

## Status

Status: Accepted
Date: 2025-12-01
Authors: Wordloom Dev (Plan_121)

## Context

Plan121 reviewed the inline Block editor after Plan120 landed and highlighted a new set of UX gaps (see `assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_121_BlockModifications+.md`). Screenshots and notes called out:

1. Clicking a heading made the entire block “弹一下”：view/edit used different fonts, padding, and borders, so the text looked like it changed clothes.
2. The micro editor textarea always reserved three rows, even for empty titles, creating a large blank area that broke the flowing-document feel.
3. Clock/Delete icons and the grey background consumed line height, making titles shift downward whenever edit mode started.
4. The inline `+` divider rendered immediately before the very first block, visually stealing space from the page top.

These were all UI polish issues; Domain contracts and ports remained correct after ADR-128. Plan121 therefore focused on refactoring the BlockList/BlockRenderer front-end while keeping Create/UpdateBlockUseCase untouched.

## Decision

1. **Shared text shells for view & edit**
   - Introduced `.textBlockShell` (paragraph + heading variants) so both reading and editing states reuse identical padding, border width, and typography. Editing now only toggles `.textBlockShellEditing`, which swaps background/border colors without changing layout.
   - Heading shells carry `data-heading-level` to apply level-specific spacing while still using the same `.headingLevelN` class whether the user is reading or typing.

2. **AutoSize micro editor**
   - Replaced the old fixed-height textarea with a reusable `AutoSizeTextarea` (minRows=1, maxRows=3, `font: inherit`). The component sets height from `scrollHeight`, so headings start at a single line and only grow as needed. Overflow is hidden to prevent the three-row blank gap described in Plan121.

3. **Hover-only icons & shell background**
   - Timestamp/Delete icons remain absolutely positioned but now live within the same shell space; opacity switches to 1 only on hover or focus, aligning with Plan121’s “icon贴边且不占行高” rule.
   - The background/outline changes are limited to hover/edit states, eliminating the “白底卡片 + 三层阴影” pop effect.

4. **Remove top inline handle**
   - BlockList skips rendering the inline `+` row before the first block. Subsequent gaps still expose the handle, so inserting between blocks works as before while the top of the document stays clean.

5. **Documentation sync**
   - Added `block_editor_plan121_micro_editor` entries to VISUAL/HEXAGONAL/DDD RULES so future iterations know that AutoSize/layout tweaks are UI-only and must not introduce new ports.

## Consequences

- Heading/paragraph blocks now look identical between read/edit states, so clicking a title no longer triggers a noticeable layout jump.
- Micro editors occupy only the text they need, reducing visual noise and keeping the “流动文档” illusion intact.
- Icon visibility and hover backgrounds are scoped to shells, preserving document rhythm while still exposing actions when required.
- Removing the first inline handle cleans up the top of the page without affecting CreateBlockUseCase; inserting at the top is still achievable via slash commands or the main CTA.
- No backend or application-layer changes were required. All adjustments live in `frontend/src/features/block/ui` and are guarded by the new RULES sections.

## References

- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_121_BlockModifications+.md
- frontend/src/features/block/ui/BlockList.tsx
- frontend/src/features/block/ui/BlockRenderer.tsx
- frontend/src/features/block/ui/BlockList.module.css
- assets/docs/VISUAL_RULES.yaml (`block_editor_plan121_micro_editor`)
- assets/docs/HEXAGONAL_RULES.yaml (`block_editor_plan121_micro_editor_contract`)
- assets/docs/DDD_RULES.yaml (`POLICY-BLOCK-PLAN121-MICRO-EDITOR`)
