# ADR-128 Plan120 Block Editor Refinement

## Status

Status: Accepted
Date: 2025-12-01
Authors: Wordloom Dev (Plan_120)

## Context

Plan120 asked the inline Block editor to feel like a flowing document page instead of stacked inputs. During QA we captured two regressions:

1. **Screenshot #1 (常驻横线)** – Inline `+` handles and paragraph textareas were rendering permanent divider lines, violating Plan120’s "only highlight the active block" rule from `Plan_120_BlockModifications.md`.
2. **Screenshot #2 (无法插入 1/2/3 级标题)** – Creating heading blocks via Slash/inline menus failed at runtime because the request omitted `heading_level`, so the backend defaulted to level 2 and rejected the payload.

Neither issue required new Domain capabilities, but both needed UI/adapter fixes plus documentation updates so future iterations don’t regress.

## Decision

1. **Paper container + spacing parity**
   - `frontend/src/features/block/ui/BlockList.module.css` now enforces the 24×40px "paper" padding, 6px block spacing, and hover/edit-only outlines specified in Plan120. Inline insert dividers stay transparent until hover/focus, eliminating the always-on grey rules from Screenshot #1.
   - Paragraph textareas no longer own a default bottom border; focus cues come from the block background, matching the spec and removing extra lines in screenshots.

2. **Heading typography alignment**
   - `.blockHeading1/2/3` line-heights and margins match Plan120 (20px/18px/15px at 1.5/1.5/1.6 line-height with 12px/10px/8px top margins). This keeps headings visually attached to their following paragraphs without touching Domain data.

3. **Slash menu + descriptions**
   - The malformed CSS block was rewritten so slash menu items reliably display label + description + shortcut hints. Empty states use a single muted message, ensuring command previews remain informative while staying within UI scope.

4. **Heading creation contract fix**
   - Both `frontend/src/app/admin/books/[bookId]/page.tsx` and `/admin/blocks/page.tsx` now pass the requested heading level through `BlockInsertOptions.headingLevel`, writing the value into `content.level` and `CreateBlockRequest.heading_level`. This resolves Screenshot #2 and documents the requirement inside `HEXAGONAL_RULES.yaml` + `DDD_RULES.yaml`.

5. **Rule synchronization**
   - `VISUAL_RULES.yaml`, `HEXAGONAL_RULES.yaml`, and `DDD_RULES.yaml` gained dedicated Plan120 sections so future contributors know these changes are UI-only and still rely on existing UseCases.

## Consequences

- Writers see the intended "paper" layout with minimally intrusive dividers, and hover/focus affordances no longer conflict with the spec.
- Heading insertion works via slash menu, inline `+`, and bottom CTA because adapters always send the correct level metadata.
- Documenting the fixes in all three RULES files and ADR-128 prevents silent regressions (e.g., forgetting `heading_level` when adding a new insertion path).
- No backend changes were necessary; Domain contracts stay untouched while UI polish and adapter correctness improve.

## References

- Screenshot #1 / Screenshot #2 (Plan120 QA captures)
- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_120_BlockModifications.md
- assets/docs/VISUAL_RULES.yaml (`block_editor_plan120_refinement`)
- assets/docs/HEXAGONAL_RULES.yaml (`block_editor_plan120_contract`)
- assets/docs/DDD_RULES.yaml (`POLICY-BLOCK-PLAN120-UI-ONLY`)
- frontend/src/features/block/ui/BlockList.module.css
- frontend/src/app/admin/books/[bookId]/page.tsx
- frontend/src/app/admin/blocks/page.tsx
