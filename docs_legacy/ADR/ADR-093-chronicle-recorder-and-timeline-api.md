# ADR-093: Chronicle Recorder and Timeline API

- Status: Accepted
- Date: 2025-11-23
- Drivers: Plan42 Chronicle timeline, Plan33 audit readiness
- Stakeholders: Backend (Domain/Infra), Frontend (Timeline UI), Product/Compliance

## Context

Library, Bookshelf, and Book aggregates now emit rich domain events (creation, move, basement entry/exit, deletion), but the platform lacked a canonical audit trail to answer "what happened to this book?" UI mockups for the Chronicle page and per-book timeline were blocked because event payloads were scattered across logs, ad-hoc tables, or not persisted at all. Compliance workstreams also require an immutable ledger of lifecycle changes with actor attribution and pagination. Previous attempts to poll individual aggregates could not reproduce ordering, and there was no API for the frontend to consume a consolidated stream.

## Decision

1. Introduce a dedicated Chronicle module (domain + application + router) that defines `ChronicleEvent` value objects, a `ChronicleEventType` enum, and the async `ChronicleRepositoryPort` for persistence.
2. Implement `SQLAlchemyChronicleRepository` backed by the `chronicle_events` table (`ChronicleEventModel`) with indexes on `(book_id, occurred_at)` and `(event_type, occurred_at)` plus JSONB payload storage for bookshelf snapshots.
3. Add application services:
   - `ChronicleRecorderService` to create and save domain-specific events such as BOOK_CREATED, MOVED, BASEMENT, RESTORED, DELETED, BLOCK_STATUS_CHANGED, and BOOK_OPENED.
   - `ChronicleQueryService` to list book events with server-side pagination (offset/limit) and optional event-type filters.
4. Wire the event bus (`EventHandlerRegistry`) so Book lifecycle events automatically record Chronicle entries without router involvement; transient HTTP clients only handle `POST /api/v1/chronicle/book-opened` for explicit "user viewed" markers.
5. Expose a Timeline API: `GET /api/v1/chronicle/books/{book_id}/events?page&size&event_types[]` returning Pagination Contract V2 `{items,total,page,size,has_more}` with normalized DTOs.
6. Extend the DI container to resolve Chronicle services/repositories for routers, tests, and event handlers; provide integration tests for recorder, handlers, router serialization, and repository queries.
7. Document the flow in DDD/HEXAGONAL/VISUAL rules to keep domain contracts, adapter responsibilities, and UI guidelines in sync with ADR-093.

## Consequences

- Positive:
  - Every meaningful book lifecycle event now lands in a single chronicle_events table, enabling UI timelines, compliance exports, and analytics without rehydrating aggregates.
  - Event bus decoupling keeps domain logic unchanged; recorder service can evolve (rate limits, dedupe) without editing each use case.
  - Frontend receives a stable paginated API and can request targeted event types (e.g., exclude BOOK_OPENED).
- Negative / Risks:
  - Chronicle table can grow quickly; without retention policies or archiving the table may affect query latency.
  - Recorder currently trusts upstream timestamps/payloads; malformed events propagate unless validation is tightened.
  - Book-only focus means Bookshelf or Library level actions still require derived book events to show up (future enhancement).

## Implementation Notes

- Domain: `ChronicleEvent` dataclass enforces immutable payloads; `ChronicleEventType` enumerates current and reserved events (FOCUS_STARTED/ENDED placeholder for Plan33 focus sessions).
- Infrastructure: `ChronicleEventModel` stores payload as JSONB; migrations create supporting indexes to make `list_by_book` and `list_by_time_range` efficient.
- Application: Recorder helper methods accept IDs/timestamps so event handlers can forward domain event data verbatim; query service simply proxies to the repository, keeping read concerns simple.
- Event Bus: Handler functions (`chronicle_book_created`, `chronicle_book_moved`, etc.) reuse a shared `_record` helper that opens an AsyncSession, constructs the repository/service, and logs failures without bubbling exceptions back to the main bus.
- Router: `/chronicle/book-opened` endpoint is intentionally unauthenticated for now (actor optional); pagination uses `has_more = offset + len(items) < total` with DTO mapping via `ChronicleEventRead`.
- DI: `DIContainer.get_chronicle_recorder_service()` and `.get_chronicle_query_service()` instantiate repositories with scoped sessions so routers/tests can depend on stable factories.

## Testing & Verification

- Unit tests cover recorder methods, query pagination, router contract (page/size/has_more, enum filtering), and event handlers via monkeypatched `_record`.
- Repository adapter tests (to be expanded) ensure JSON payload round-trip and ordering semantics.
- Pytest target `api/app/tests/test_chronicle` is now part of CI smoke runs (12 tests passing as of Nov 23, 2025).

## Rollout & Follow-up

1. Backend
   - ✅ Chronicle module merged with DI + event bus wiring.
   - ✅ Timeline API deployed behind `/api/v1/chronicle`.
   - ⏳ Add retention/archival strategy + metrics (future ADR if needed).
2. Frontend
   - ⏳ Implement `useChronicleTimeline` hook + Timeline list component and surface it in Book detail + `/admin/chronicle` per Plan42.
3. Documentation
   - ✅ This ADR-093 captures architecture decisions.
   - ✅ Synchronize DDD/HEXAGONAL/VISUAL rules with Chronicle domain and UI guidelines.
4. Risk Mitigation
   - Track table size + query latency; consider time-partitioned tables or scheduled pruning past retention windows once requirements clarify.
   - Add optional rate limiting / dedupe in recorder before exposing public write endpoints beyond BOOK_OPENED.

## Future Work

- Extend Chronicle to capture Bookshelf-level and Media-related events once corresponding domain events exist.
- Introduce batch export endpoints and CSV/ICS downloads for compliance.
- Add search/filter by actor and integrate with Stats module for trend charts.
- Implement notification hooks when critical events (e.g., book restored from basement) occur.
- Evaluate storing derived metrics (e.g., dwell time between open and focus events) after FOCUS_* events launch.
