# ADR-075: Basement Virtual Integration & API Prefix Consistency Reinforcement

Date: 2025-11-19
Status: Accepted
Deciders: Wordloom Core Team
Tags: frontend, ddd, ux, api-prefix, basement, soft-delete

## 1. Context
During Week 2 integration, a misleading "libraries load failure" was traced to a raw fetch for Basement deleted books omitting the required `/api/v1` prefix. Basement is a virtual construct in the UI (a consolidated soft-delete recovery surface) and not a real Aggregate Root. Prior documentation lacked an explicit visual integration rule and a cross-layer statement preventing prefix omissions in ad‑hoc fetches.

## 2. Problem
1. UX Separation: Basement card was visually detached (rendered above the grid) creating layout shift and unclear relationship to library collection.
2. Error Coupling: A failed Basement fetch cascaded into a perceived library failure because shared error interceptors lacked isolation.
3. Prefix Drift Risk: Manual fetches for Basement endpoints risk bypassing standardized API client composition, reintroducing prefix omissions.
4. Documentation Gap: HEXAGONAL / DDD / VISUAL rules referenced Basement existence but not its grid embedding semantics or exclusion from counts.

## 3. Forces / Drivers
- Consistency: Users expect all "containers" to appear within one visual grid.
- Clarity: Basement must signal its immutable, non-count status (🔒) and not affect pagination or library metrics.
- Reliability: Enforcing prefix usage across raw fetches reduces CORS/404 noise and false failure attribution.
- Extensibility: Clean separation allows optional future migration of Basement stats into Search adapters without domain leakage.

## 4. Decision
Embed Basement as the first immutable virtual card inside the libraries grid (vertical & horizontal) using `LibraryList.extraFirst`. Introduce skeleton loading preserving grid layout. Formalize prefix consistency (POLICY-013 + RULE_API_PREFIX_001) and add Basement visual integration policy (POLICY-014) + grid rule (RULE_BASEMENT_GRID_001). Errors in Basement stats are isolated to its card.

## 5. Implementation Summary
- Code Changes:
  - `LibraryList.tsx`: added `extraFirst` prop + skeleton placeholders; basement rendered inline.
  - `LibraryMainWidget.tsx` + `page.tsx`: removed standalone Basement section; inject card via `extraFirst`.
- Rules Updates:
  - VISUAL_RULES.yaml: Added `RULE_BASEMENT_GRID_001`.
  - DDD_RULES.yaml: Added `POLICY-014-BASEMENT-VISUAL-INTEGRATION`.
  - HEXAGONAL_RULES.yaml: Added `basement_visual_grid_integration_status` metadata.
- Prefix Enforcement: All Basement-related fetches must reuse shared configuration `(base_url + api_prefix + path)`; raw URL concatenations prohibited.
- Accessibility: Card remains keyboard-focusable; `aria-label="Basement 回收站入口"` retained.

## 6. Consequences
### Positive
- Eliminates layout jump; one cohesive mental model for library containers.
- Prevents Basement fetch failure from masking core library list (error isolation).
- Reduces future regression risk via explicit cross-file policies.
- Skeleton loading enhances perceived performance (no spinner empty hole).

### Neutral / Trade-offs
- Slight increase in LibraryList responsibility (now handles optional first item + skeleton). Acceptable until a future refactor extracts a dedicated Grid component.
- Additional policy/rule entries increase documentation volume; mitigated by clear anchors and consistent naming.

### Negative
- Added complexity in LibraryList may require test coverage updates.
- Horizontal layout visually treats Basement differently (no row mixing). Minor and acceptable.

## 7. Alternatives Considered
| Option | Description | Outcome |
|--------|-------------|---------|
| A | Keep Basement above grid (status quo) | Rejected: layout shift + unclear semantics |
| B | Separate Basement page only (no card) | Rejected: discoverability drop |
| C | Place Basement at end of grid | Rejected: breaks "utility first" / quick access convention |
| D | Treat Basement as pseudo-library in backend | Rejected: pollutes domain model, violates DDD boundaries |

## 8. Migration / Rollout
No data migration. Redeploy frontend; verify:
1. Libraries load with skeleton.
2. Basement displays counts (0 allowed) and navigates to `/admin/basement`.
3. Deliberately break Basement endpoint → only that card errors; libraries remain intact.
4. Search for occurrences of `books/deleted` to confirm no raw prefix omissions.

## 9. Testing Guidance
- Unit: LibraryList renders `extraFirst` + skeleton count.
- Integration: Navigate `/admin/libraries`; mock Basement failure → expect fallback text.
- Accessibility: Tab order reaches Basement first; Enter activates navigation.
- Performance: Measure LCP before/after; skeleton should reduce perceived wait vs Spinner.

## 10. Future Work
- Virtual scrolling when library count > 50 with fixed first item.
- Telemetry: Track Basement card interaction + recovery actions.
- Merge Basement stats query into Search adapter (phase after media/tag completion).
- Add CI rule scanning for `fetch(` usages verifying prefix composition.

## 11. References
- POLICY-013-API-PREFIX-CONSISTENCY (DDD_RULES.yaml)
- POLICY-014-BASEMENT-VISUAL-INTEGRATION (DDD_RULES.yaml)
- RULE_API_PREFIX_001 (VISUAL_RULES.yaml)
- RULE_BASEMENT_GRID_001 (VISUAL_RULES.yaml)
- HEXAGONAL_RULES metadata: `api_prefix_consistency_issue`, `basement_visual_grid_integration_status`
- ADR-072-basement-ux-and-restore-flows.md

## 12. Decision Log
- 2025-11-19: Accepted (implementation complete + documentation updated).

---
This ADR codifies visual + infrastructural alignment ensuring Basement remains a purely presentational recovery surface without polluting domain boundaries and safeguards future feature velocity.
