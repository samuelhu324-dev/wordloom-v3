# ADR-079: Pagination Contract V2, Preview Card Enhancements, Layout Toggle, Placeholder Cover Strategy, V1 Sunset Plan

Status: Accepted
Date: 2025-11-20
Decision Drivers:
- Need consistent pagination across all list endpoints (avoid ad-hoc `{items,total}` parsing & front-end hasMore inference)
- Upgrade book & bookshelf preview experience (placeholder cover + status badges) without polluting domain models
- Support user-controlled layout (grid vs horizontal) with persistent preference and zero domain coupling
- Define clear deprecation timeline for legacy Pagination V1 and mixed enum casing

## Context
Prior implementation returned `{items,total}` only. UI inferred `hasMore` by comparing page size vs item count, causing edge errors and double-fetch near boundaries. Enum casing was inconsistently handled (some uppercase leaked). Placeholder covers were generated ad hoc inside multiple components.

## Decision
1. Pagination Contract V2 shape:
```json
{
  "items": [...],
  "total": 123,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```
2. Backend becomes source of truth for `has_more` (Repository layer calculation or prefetch strategy). Frontend removes inference logic by Dec 1, 2025.
3. Legacy V1 `{items,total}` marked deprecated immediately; full sunset Dec 15, 2025.
4. Enum casing: Domain enums remain UPPER_SNAKE_CASE; transport layer strictly lower_case; adapters perform conversion; UI free to display.
5. Placeholder cover strategy: Pure front-end deterministic hash (FNV-1a on `title|id`) → palette + glyph (first letter). No domain/storage field added. Future real cover integration stays adapter-composed (`cover_url`).
6. Layout toggle: Component-level state + localStorage key (`bookLayoutMode`) controlling `horizontal` vs `grid` presentation; no API field or domain concept introduced.
7. Sunset timeline codified across VISUAL_RULES, HEXAGONAL_RULES, DDD_RULES (added rules & conventions). CI tests will fail if `has_more` missing post-Nov 25.

## Alternatives Considered
- Inferring `has_more` on frontend (kept for V1 but error-prone) → rejected for precision & contract clarity.
- Embedding cover glyph/color into backend response → rejected (presentation concern, violates hexagonal separation).
- Adding enum mapping helpers inside domain objects → rejected (leaks transport concerns into domain layer).

## Consequences
Positive:
- Uniform pagination improves caching keys, testability, UI predictability.
- Clear deprecation path reduces long-term maintenance burden.
- Presentation features (cover, layout) isolated from domain prevents model bloat.
- Enum conversion centralized: fewer accidental uppercase leaks in transport.
Risks:
- Short-term dual handling until Dec 15 (compat code removal required).
- Need repository updates to compute `has_more` efficiently (avoid counting on large tables without indexes).
Mitigations:
- Add necessary indexes (library_id, bookshelf_id, soft_deleted_at) already listed in HEXAGONAL_RULES.
- Mark all temporary inference sections with `TODO:REMOVE-V1-COMPAT`.

## Implementation Steps
1. Backend: Add `has_more` field to all list endpoints (books, bookshelves, blocks, tags, media) by Nov 22.
2. Frontend: Replace inference with direct consumption; remove fallback by Dec 1.
3. Tests: Add backend unit tests for boundary pages; add frontend query hook tests ensuring stable key composition.
4. Docs: Completed (VISUAL_RULES.yaml, HEXAGONAL_RULES.yaml, DDD_RULES.yaml updated; this ADR created).
5. Clean-up: Remove any `total_count` remnants; ensure only `total` used.

## Sunset Timeline (Detailed)
- Nov 20: ADR accepted; V2 contract published.
- Nov 22: All backend endpoints emit `has_more`.
- Nov 25: CI asserts presence of `has_more` (failure if absent).
- Dec 01: Frontend removes inference fallback.
- Dec 15: Delete all `TODO:REMOVE-V1-COMPAT` comments; remove any conditional parsing of V1 shape.

## Testing Guidelines
Backend:
- Page 1 with full page_size and remaining records → `has_more: true`.
- Last page (page*page_size == total) → `has_more: false`.
- Edge case: Empty results page >1 after deletions → items=[], `has_more: false`.
Frontend:
- Hook returns stable tuple `[data.items, data.total, data.has_more]`.
- No length-based hasMore logic after Dec 1.

## Monitoring & Metrics
- Track pagination endpoint median latency pre/post change.
- Log occurrences of missing `has_more` during transition (should drop to 0 after Nov 25).
- UI error banner frequency (expected reduction due to more predictable end-of-list behavior).

## Future Extensions
- Cursor-based pagination for very large tables (optional second contract after stabilization).
- Cover glyph theming (dark/light adaptive contrast).
- Animated layout transitions (CSS transform) once stable.

## References
- VISUAL_RULES.yaml: RULE_API_010_CONTRACT_SYNC et al.
- HEXAGONAL_RULES.yaml: RULE_PAGINATION_CONTRACT_V2_001, RULE_ENUM_CASING_ADAPTER_001.
- DDD_RULES.yaml: CONVENTION-RESPONSES-001, CONVENTION-ENUMS-001 updated.
- Eric Evans, Domain-Driven Design (Aggregates, boundaries).

## Decision Record
Accepted unanimously Nov 20, 2025. Author: System sync agent.
