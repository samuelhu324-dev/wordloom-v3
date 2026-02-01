# ADR-107 Plan82 Hidden Blocks Paragraph Editing Flow

## Status

Status: Proposed
Date: 2025-11-27
Authors: Wordloom Dev (Plan_82)

## Context

Plan80 shipped the “inline paper” visual treatment for the Blocks tab, but every block still rendered an always-on `<textarea>`, which looked like multiple form inputs stacked together. Product design (Plan_82) requested a calmer reading surface where paragraphs look continuous until the user explicitly edits one block. The goals:

- Make BlockList feel like a document: no card chrome, no permanent inputs, only faint separators.
- Allow editing a single block at a time, so keyboard focus and hover toolbars feel deliberate.
- Keep SAVE semantics intact (Ctrl/Cmd+S, blur auto-save, SaveAll button) without adding new backend endpoints.
- Document the new responsibilities across VISUAL/HEXAGONAL/DDD rule sets to avoid future regressions.

## Decision

1. **Reading vs Editing modes**
   - BlockList maintains a UI-only `editingBlockId`. Blocks render as paragraph `<div role="button">` when not editing, preserving whitespace via `white-space: pre-wrap`.
   - Clicking, pressing Enter/Space, or invoking keyboard shortcuts swaps the block into editing mode, rendering the existing textarea and auto-focusing it.
   - Only one block can be editing at a time; switching focus triggers the previous block’s blur handler.

2. **Save contract reuse**
   - Blur, Ctrl/Cmd+S, and the parent SAVE button all delegate to the existing `useUpdateBlock` mutation; no new batch endpoint is introduced.
   - The BlockList exposes a `saveAll` imperative handle (same as Plan80) that simply awaits each registered save handler, ensuring domain/application contracts remain unchanged.

3. **UI states stay in the adapter**
   - `editingBlockId`, hover opacity, placeholder text, and inline CTA placement remain in the React layer and are not persisted to Block meta/DTOs.
   - Documentation (VISUAL_RULES, HEXAGONAL_RULES, DDD_RULES) now contains Plan82-specific clauses to prevent future attempts to promote these concerns into the domain model.

## Consequences

- Blocks visually appear as continuous paragraphs, matching the “无 block 感” requirement while keeping editing interactions familiar.
- The SAVE button and keyboard shortcuts continue to work because they reuse the existing mutation layer; QA only needs to cover focus switches and blur saves.
- Future variants (inline media preview, comment pills, etc.) must extend this ADR or add follow-up ADRs to document any adapter/domain impact.

## References

- assets/docs/QuickLog/D39-45- WordloomDev/Plan_82_HiddenBlocks++.md
- assets/docs/VISUAL_RULES.yaml (RULE_BLOCK_PLAN82_PARAGRAPH_EDITING)
- assets/docs/HEXAGONAL_RULES.yaml (plan82_paragraph_editing_flow)
- assets/docs/DDD_RULES.yaml (POLICY-BLOCK-PLAN82-EDITING-FLOW)
- frontend/src/features/block/ui/BlockList.tsx
