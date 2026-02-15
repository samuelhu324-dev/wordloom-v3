# ADR-099: Book Detail Workspace Tabs Integration

- Status: Accepted (Nov 26, 2025)
- Deciders: Wordloom Core Team
- Context: Admin book detail workspace, Option A iteration, VISUAL/DDD/HEXAGONAL rule sync
- Related: ADR-077 (Book Preview Cards), ADR-092 (Book Maturity Segmentation), ADR-093 (Chronicle Timeline API)

## Context

The previous book detail experience required operators to click a "进入块工作台" button that redirected to `/admin/blocks`. That split view forced context switching between book metadata, block editing, and Chronicle history, and made it hard to keep the book’s aggregate context visible while editing. Recent stakeholder feedback preferred keeping all book operations inside `/admin/books/{bookId}` with clear tabs mirroring the design mockups (概览 / 块编辑 / 时间线).

## Decision

1. **Embed Workspace Tabs**: `/admin/books/{bookId}` now renders three tabs (Overview, Blocks, Timeline). Local state backed by `localStorage` (`wordloom.book.detail.tab:{bookId}`) remembers the last tab per book while resetting to Overview when switching entities.
2. **Reuse Existing Ports**: The page orchestrates `useBook`, `useBookshelf`, `useLibrary`, `usePaginatedBlocksPhase0`, and `useChronicleTimeline` hooks without adding new endpoints. InlineCreateBar, BlockList, BlockEditor, and DeletedBlocksPanel continue to call their existing mutation ports.
3. **Rules Synchronised**: `HEXAGONAL_RULES.yaml`, `VISUAL_RULES.yaml`, and `DDD_RULES.yaml` document the integrated workspace, tab behaviour, and aggregate boundaries to prevent future regressions toward a standalone blocks route.

## Rationale

- Keeps operators inside the book context, making status, library/Bookshelf info, and risk notes visible while editing blocks.
- Reduces navigation hops and aligns with Option A mockups that highlighted tabs rather than deep links.
- Ensures we do not proliferate new ports or DTOs for metrics/timeline; the UI composes existing data sources and placeholders until richer telemetry ships.

## Scope

- Frontend: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`.
- Documentation: `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`.
- No backend code changes required.

## Non-Goals

- Removing the legacy `/admin/blocks` route (kept temporarily for parity checks).
- Delivering new maturity or analytics metrics (placeholders remain until corresponding use cases are ready).
- Implementing Chronicle timeline filters beyond existing pagination.

## Implementation Notes

- Hero card shows library/Bookshelf lineage, maturity/status pills, and two rows of metrics cards. Metrics currently display placeholders where backend figures are pending.
- The Overview tab renders section cards plus a sticky InfoPanel summarising IDs, timestamps, and block counts.
- The Blocks tab keeps pagination (20/block per page) and reuses InlineCreateBar → BlockList → BlockEditor → DeletedBlocksPanel flow; `useDeleteBlock` handles removals, and page switches reset editing state.
- The Timeline tab renders `ChronicleTimelineList` with the same DTO contract as `/admin/chronicle` and keeps the InfoPanel visible for context.
- Responsive layout collapses to a single column under 1100px and reduces padding below 768px.

## Testing

- Manual verification of tab switching persistence, pagination controls, and Chronicle preview under mocked data.
- Follow-up automated coverage planned for tab state persistence and snapshot tests for the three tab panels.

## Rollback

Reinstate the prior book detail layout, restore the "进入块工作台" navigation button, and revert the documentation updates. No migrations are needed.

## References

- `frontend/src/app/admin/books/[bookId]/page.tsx`
- `frontend/src/app/admin/books/[bookId]/page.module.css`
- `frontend/src/features/block/ui/InlineCreateBar.tsx`
- `frontend/src/features/block/ui/BlockList.tsx`
- `frontend/src/features/block/ui/BlockEditor.tsx`
- `frontend/src/features/block/ui/DeletedBlocksPanel.tsx`
- `frontend/src/features/chronicle/ChronicleTimelineList.tsx`
- `assets/docs/HEXAGONAL_RULES.yaml`
- `assets/docs/VISUAL_RULES.yaml`
- `assets/docs/DDD_RULES.yaml`
