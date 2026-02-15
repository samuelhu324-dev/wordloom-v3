# ADR-112: Book Overview Recent Events & Structure Tasks

- Status: Accepted (Nov 28, 2025)
- Deciders: Wordloom Core Team
- Context: Plan_96 (Timeline & Maturity Integration+), Plan_92 (Book maturity scoring), Plan_86 (Chronicle timeline), Plan_88 (Lucide cover icons)
- Related: ADR-092 (Book maturity segmentation), ADR-093 (Chronicle timeline API), ADR-099 (Book workspace tabs), ADR-111 (Book maturity & timeline integration); DDD_RULES `POLICY-BOOK-OVERVIEW-RECENT-CHRONICLE` / `POLICY-BOOK-OVERVIEW-NEXT-STEPS`; HEXAGONAL_RULES `chronicle_timeline_strategy` / `book_workspace_tabs_integration`; VISUAL_RULES `book_workspace_tabs_visual_rules`

## Problem

Even after ADR-111 unified maturity coverage and timeline contracts, the Book workspace Overview tab still lacked guided signals:

1. **Recent timeline visibility** – Overview required designers to peek into the Chronicle tab to confirm whether migrations or bookshelf moves happened recently. UI widgets were splicing TanStack cache or duplicating timeline cards, risking divergence from ChronicleQueryService.
2. **Actionable maturity steps** – Teams needed a quick checklist that maps maturity scoring factors (title, summary, tags, cover, blocks, visits) to concrete next steps. Without it, reviewers had to consult Plan_92 manually, and the UI offered no “why is this book still growing?” hints.
3. **Stage change observability** – Backend now emits `book_stage_changed`, but the frontend enum and UI labels were incomplete, so stage migrations could not surface in either timeline or overview.

## Decision

1. **Introduce a dedicated `useRecentChronicleEvents` hook** that reuses `ChronicleQueryService.list_book_events` with `size=5` and the default `book_*` event set (stage, move, basement, restore, delete, block state). Visits (`book_opened`) stay opt-in for the full timeline, keeping Overview noise-free.
2. **Extend Chronicle DTOs on the frontend** to include the `book_stage_changed` enum/value, icons, labels, and payload summarisation (`Seed → Stable · Score 72 · manual`). Both Overview and Timeline components share the same formatter.
3. **Replace the old coverage placeholder with a maturity score indicator** derived directly from `BookDto.maturityScore`, while counters now highlight stage, score, block count, total chronicle events, latest event time, 90-day visits, and last visit.
4. **Add a UI-only `NextStepsChecklist` component** that maps `BookDto` fields (summary, tags, cover icon, block_count, visitCount90d, maturityScore, legacyFlag) to up to five actionable tasks. Legacy books switch to “review & restore” hints; other stages prioritise unfinished fundamentals (summary, tags, cover, blocks ≥20, visits, score ≥70). No new backend fields are introduced.
5. **Document the contracts** across DDD/Hex/Visual rules and capture this ADR to prevent future regressions (e.g., reintroducing visit events by default or persisting checklist state).

## Consequences

- Overview now consumes Chronicle data via a single query path, ensuring pagination, filtering, and future schema changes stay consistent with the Timeline tab.
- Teams receive instant maturity guidance without reading Plan_92; checklists stay client-side, so domain aggregates remain untouched.
- Stage change payloads become visible in both overview summaries and the paginated timeline, improving audit parity.
- The maturity progress bar no longer hand-waves “coverage”; it reflects the actual 0-100 score returned by backend use cases, reinforcing the scoring policy.
- Additional UI work (new component + styling) slightly increases bundle size, but removes duplicated logic previously scattered across cards.

## Implementation Notes

- **Frontend**
  - Added `ChronicleEventType` union variant `'book_stage_changed'` and associated label/icon handling (LineChart) within `ChronicleTimelineList` and overview summariser.
  - Exposed `CHRONICLE_DEFAULT_EVENT_TYPES` plus the new `useRecentChronicleEvents` hook from `features/chronicle/model/hooks.ts`.
  - Refactored `app/admin/books/[bookId]/page.tsx` to consume the new hook, render the refreshed metrics, insert the "查看全部" CTA, and wire in `NextStepsChecklist`.
  - Created `NextStepsChecklist` component + CSS module under `features/book/ui`, sorting unfinished tasks to the top and providing muted styling for completed items.
  - Updated styles for the recent events list (flex column, subtle borders) and ensured progress labels read "Maturity".

- **Rules & Docs**
  - DDD_RULES adds `POLICY-BOOK-OVERVIEW-RECENT-CHRONICLE` and `POLICY-BOOK-OVERVIEW-NEXT-STEPS` to lock data sources and UI-only derivations.
  - HEXAGONAL_RULES refreshes `chronicle_timeline_strategy` (new default types, overview usage) and `book_workspace_tabs_integration` (overview responsibilities).
  - VISUAL_RULES refreshes hero metrics, maturity indicator semantics, the recent events card description, and the new structure task checklist behaviour.

## Alternatives Considered

1. **Bundling recent events inside the Book DTO** – Rejected to avoid coupling the Book aggregate to Chronicle data and to keep pagination logic within the dedicated query port.
2. **Persisting checklist progress on the server** – Discarded because the tasks are derived directly from live DTO fields; storing booleans would duplicate state and demand new endpoints.
3. **Keeping visit events in the overview feed** – Trialled but noisy; audit logs become unreadable for active books. The include-visits toggle remains exclusive to the full timeline tab.

## Future Work

- Add a hover tooltip to maturity counters, surfacing the scoring breakdown returned by backend services.
- Explore exposing stage change triggers (`trigger` payload) as badges in the overview card when we unify manual/automatic migrations.
- Consider surfacing open TODO counts in the checklist once the Todo projection port graduates from Stage 0.
