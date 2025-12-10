# ADR-106 Plan80 Hidden Blocks Inline Paper Layout

## Status

Status: Proposed
Date: 2025-11-27
Authors: Wordloom Dev (Plan_80)

## Context

The Blocks tab recently converged into the unified Book workspace (ADR-099).  The existing BlockList still looked like stacked cards with constant chrome, which clashed with the Plan80 visual direction described in the VISUAL_RULES log ("看起来像段落").  Product design asked for a lighter flow that:

- removes card boxes and makes every block resemble inline paper strips;
- hides toolbars until the cursor hovers over a block, removing persistent icon noise;
- moves the add CTA to the flow bottom, mirroring document editors;
- keeps the SAVE affordance (Ctrl+S + button) but ensures it does not require extra backend calls; and
- documents the UI-only nature of these changes so the domain/application layers remain untouched.

The documentation set (VISUAL_RULES / HEXAGONAL_RULES / DDD_RULES) and ADR catalog did not yet explain how Plan80 translates to architecture decisions, making future contributors prone to re-introducing card chrome or extra ports.

## Decision

1. **Inline paper rendering**
   - `frontend/src/features/block/ui/BlockList.tsx` now renders transparent wrappers with textarea-only blocks.  Focus states show a single underline to emulate notebook paper.
   - Blocks no longer display index or heavy shadows; spacing relies on gap tokens defined in `BlockList.module.css`.

2. **Hover-only actions + bottom CTA**
   - Action icons (delete, duplicate, etc.) receive `opacity: 0` by default and fade in when the row is hovered or focused.
   - The add-entry control becomes a bottom "＋ 添加一段文字" button spanning the list width, still calling `useCreateBlock`.

3. **Save affordance consolidation**
   - `BlockList` exposes a `saveAll` handle so parent tabs wire the SAVE button and `Ctrl+S` shortcut without duplicating logic.  No new backend endpoint is created; the feature simply flushes pending block mutations through existing hooks.

4. **Domain boundary reinforcement**
   - All styling/interaction tweaks stay in the UI adapter.  No additional fields are added to Block aggregates, DTOs, or repositories.  Hover/placeholder state must never be persisted.
   - VISUAL_RULES, HEXAGONAL_RULES, and DDD_RULES gain explicit Plan80 sections to remind teams this is an adapter concern.

## Consequences

- The Blocks tab now matches Plan80 expectations, reducing visual clutter and aligning with other inline editors in the product.
- Documentation clarifies that Plan80 is a UI-only change, preventing accidental domain drift (e.g., storing hover state in Block meta).
- Test plans should cover keyboard save (Ctrl+S) and ensure block creation still depends on `CreateBlockUseCase`.

## References

- VISUAL_RULES.yaml RULE_BLOCK_PLAN80_INLINE_PAPER
- HEXAGONAL_RULES.yaml plan80_hidden_blocks_ui
- DDD_RULES.yaml POLICY-BLOCK-PLAN80-INLINE-PAPER
- frontend/src/features/block/ui/BlockList.tsx
- frontend/src/features/block/ui/BlockList.module.css
- ADR-099-book-detail-workspace-tabs-integration.md
