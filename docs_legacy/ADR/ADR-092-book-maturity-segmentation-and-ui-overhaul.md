# ADR-092: Book Maturity Segmentation and UI Overhaul

- Status: Accepted
- Date: 2025-11-23
- Drivers: Plan39 Phase 2, Plan14 Book UX overhaul
- Stakeholders: Product (Samuel Hu), Backend (Domain/Infra teams), Frontend (UI/UX squad)

## Context

Existing Book listings presented a flat list of items regardless of lifecycle stage. Product direction (Plan14 → Plan39) requires surfacing the maturity of each Book within a Bookshelf so that teams can triage drafts, track in-progress titles, highlight launch-ready content, and keep legacy material accessible but immutable. The backend already exposed partial hints (status, timestamps) but lacked a first-class maturity concept; frontend users relied on tags and manual sorting. The lack of structure also obscured completion progress and made it impossible to enforce state-dependent capabilities such as cover configuration.

## Decision

1. Introduce a domain-level `BookMaturity` enumeration with four canonical states: `SEED`, `GROWING`, `STABLE`, `LEGACY`. Domain entities default to `SEED` on creation; migrations backfill existing rows to `seed`.
2. Formalize a unidirectional state machine: `SEED → GROWING → STABLE → LEGACY`, with `restore_from_legacy()` returning to `STABLE`. Feeds into use cases for status promotion/demotion.
3. Extend Book repositories, DTOs, and API responses to serialize `maturity` (lower_case) as part of Pagination Contract V2 `{items,total,page,page_size,has_more}`.
4. Rebuild `BookMainWidget` to group fetched items by maturity, render segmented sections, compute a SummaryBar (`progress = stable_count / (total - legacy_count)`), and expose a “load more” affordance powered by `useInfiniteBooks`.
5. Enforce capability boundaries: only `STABLE` Books surface an enabled “configure cover” button; `LEGACY` Books render as read-only (menu displays disabled controls + tooltip).

## Consequences

- Positive:
  - Teams gain immediate visibility into pipeline health (Seed ideas vs Growing drafts vs Stable launches).
  - Completion progress metrics become actionable, unlocking dashboards and review cadences.
  - State machine centralizes guard rails (e.g., cover updates limited to Stable, Legacy locked).
- Negative / Risks:
  - More complex client logic (grouping, incremental loading) increases testing surface.
  - Additional domain states require future migrations when adding new lifecycle steps.
  - Strict state machine may block exceptional workflows (e.g., reverting Stable to Growing) unless explicitly allowed.

## Implementation Notes

- Domain: `Book` entity gains maturity field and helper methods; migrations add `maturity VARCHAR(16) NOT NULL DEFAULT 'seed'` plus index `idx_books_maturity`.
- Application: `ListBooksUseCase` and adapters now return/consume Pagination V2 with `maturity`; update use case validates state transitions.
- Infrastructure: `SQLAlchemyBookRepository` maps enum to lowercase strings; FastAPI serializers rely on `to_book_response()`.
- Frontend: `useInfiniteBooks` hook wraps the paginated API; `BookMainWidget` aggregates items, shows SummaryBar, handles “Load more” button, and disables actions for Legacy items; `BookPreviewCard` adds cover button gating + fade/slide animation keyed by maturity.
- Testing: Domain tests cover valid/invalid transitions; adapter tests ensure maturity round-trip; React tests snapshot segmented rendering and disabled controls.

## Rollout

1. Phase 0 (completed): add maturity column + DTO plumbing without changing UI.
2. Phase 1 (completed): enable segmented UI + SummaryBar, keeping feature flag internal.
3. Phase 2 (current): activate Stable-only cover controls, Legacy read-only, infinite scroll + visual polish.
4. Phase 3 (planned): update DDD/Hexagonal/Visual rules and ADR documentation (this record), followed by regression testing and production launch.

## Future Work

- Add dedicated endpoints or mutations for maturity transitions with audit logging.
- Provide automatic promotion heuristics (e.g., block_count threshold) via scheduled jobs.
- Extend analytics dashboards leveraging SummaryBar metrics server-side.
- Evaluate bulk actions (multi-select) and maturity change workflows (Plan39 Phase B).
- Integrate Storybook or visual regression coverage for segmented widget themes.
