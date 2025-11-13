# ADR-027: System Rules Consolidation - Three-File Architecture

**Status:** ACCEPTED
**Date:** 2025-11-13
**Decision Date:** 2025-11-13
**Authors:** Architecture Team
**Supersedes:** None (replaces initial SYSTEM_RULES.yaml consolidation attempt)

---

## 1. Context

After completing the Hexagonal Architecture migration (8/8 steps), we needed to consolidate two massive rule documents:
- **DDD_RULES.yaml** (2483 lines): Business rules, invariants, policies, domains, implementation phases
- **HEXAGONAL_RULES.yaml** (1000+ lines): Architecture constraints, ports, adapters, testing strategy

Initial approach: Merge into single **SYSTEM_RULES.yaml**

**Problem discovered:** Merging created a 3000+ line "god file" that:
- Mixed business concerns with architecture concerns
- Made navigation difficult (search for 26 rules + 42 endpoints all in one file)
- Forced readers to context-switch constantly
- Became hard to maintain and iterate on

---

## 2. Decision

**Adopt three-file separation architecture for rule documentation:**

```
📋 DDD_RULES.yaml (2483 lines)
   ├─ Core business invariants (26 rules: RULE-001 to RULE-026)
   ├─ Business policies (14 policies: POLICY-001 to POLICY-014)
   ├─ Domain definitions (10 domains with 5-layer implementation details)
   ├─ Cross-domain events
   ├─ Implementation phases (5 phases)
   ├─ Module-level metadata (status, maturity scores, test counts)
   └─ Integration test results

🏗️ HEXAGONAL_RULES.yaml (1000+ lines)
   ├─ Hexagonal architecture rules (ports, adapters, DI)
   ├─ 8-step conversion completion status
   ├─ 42 HTTP endpoints breakdown
   ├─ 27 domain events enumeration
   ├─ Testing strategy (pyramid pattern)
   ├─ Error mapping (HTTP status codes)
   ├─ Observability requirements
   ├─ Performance optimization rules
   └─ System maturity indicators

✅ SYSTEM_RULES.yaml (deprecated - no longer exists)
   └─ Consolidated into two specialized files above
```

---

## 3. Consequences

### Advantages ✅

1. **Clear Separation of Concerns**
   - Business logic rules ← DDD_RULES.yaml
   - Architecture constraints ← HEXAGONAL_RULES.yaml
   - No context-switching needed when reading

2. **Easier Navigation & Search**
   - Developers looking for "RULE-001"? → Go to DDD_RULES.yaml
   - Developers looking for "42 endpoints"? → Go to HEXAGONAL_RULES.yaml
   - Much faster file-level searches

3. **Better Iteration & Maintenance**
   - Business rules can evolve independently from architecture
   - Architects can refactor ports/adapters without touching domain rules
   - Domain experts and infrastructure experts work in parallel

4. **Single Source of Truth Per Concern**
   - Not "which file has the endpoint list?" anymore
   - Clear expectation: Hexagonal file for architecture, DDD file for business

5. **Scalability**
   - If we add Chronicle, Search, Stats, Theme modules (Phase 2),
     we only extend DDD_RULES.yaml, not touch architecture rules
   - Clean growth pattern

### Tradeoffs & Mitigations

| Issue | Mitigation |
|-------|-----------|
| Multiple files to maintain | Cross-reference documentation (this ADR) + clear file naming |
| Reader must know which file to query | File navigation guide + inline comments in each file |
| Initial learning curve | Comprehensive navigation guide at top of each file |
| Risk of version mismatch | Both files updated together in same PR |

---

## 4. File Organization & Navigation

### DDD_RULES.yaml - When to Query?

**Query this file if you want to know:**
- ✅ "What is RULE-001?" → Search `RULE-001` in ddd.invariants
- ✅ "What happens when Bookshelf is deleted?" → Search `POLICY-003`
- ✅ "How is Library implemented (5 layers)?" → Go to `domains.library.implementation_layers`
- ✅ "What events does Tag emit?" → Go to `domains.tag.events`
- ✅ "Module completion status?" → Search `library_module_status` in metadata
- ✅ "Test file locations?" → Search `test_files` in metadata
- ✅ "Integration test results?" → Search `integration_test_status` in metadata
- ✅ "Implementation phases?" → Go to `implementation_phases` section

**File structure:**
```yaml
metadata:
  - Version info
  - Module status (Library, Bookshelf, Book, Block, Tag, Media)
  - Test counts per module
  - Integration test results (54 tests baseline)

ddd:
  invariants:
    RULE-001 to RULE-026 (26 rules)
  policies:
    POLICY-001 to POLICY-014 (14 policies)

domains:
  library:
    - implementation_layers (domain/service/repository/infrastructure/testing)
    - invariants_detailed (codes examples)
    - policies_detailed
    - events
    - children
  # Similar for: bookshelf, book, block, tag, media, chronicle, search, stats, theme

cross_domain_events:
  - BookshelfDeleted → cascade effects
  - BookDeleted → cascade effects
  # etc.

implementation_phases:
  phase_1, phase_2, phase_3, phase_4, phase_5

testing_strategy:
  - Unit tests (>= 90% coverage)
  - Integration tests (>= 80% coverage)
  # etc.

devlog_entries:
  - D30, D31, D32, D33, D34, D35, D36, D37

changelog:
  - All historical changes per date
```

### HEXAGONAL_RULES.yaml - When to Query?

**Query this file if you want to know:**
- ✅ "How many endpoints do we have?" → Go to `hexagonal_conversion_status.step_8_di_and_routers.endpoints_count`
- ✅ "What are all 42 endpoints?" → Go to `step_8.part_b_routers.endpoints_breakdown`
- ✅ "How many domain events?" → Search `total_domain_events: 27`
- ✅ "What is the testing strategy?" → Go to `hexagonal.testing`
- ✅ "Exception → HTTP status mapping?" → Go to `hexagonal.error_mapping`
- ✅ "How to implement Repository adapter?" → Go to `hexagonal.adapters.repository_adapter_pattern`
- ✅ "DI Container pattern?" → Go to `hexagonal.di.composition_root`
- ✅ "Observability requirements?" → Go to `hexagonal.observability`
- ✅ "What is Step 1/2/3...8 of migration?" → Go to `hexagonal_conversion_status`

**File structure:**
```yaml
metadata:
  - Version info
  - Endpoints count (42)
  - Domain events count (27)
  - Event handlers count (32)

hexagonal:
  ports:
    inbound: REST API, CLI, Scheduler, Test adapters
    outbound: Repository, EventBus, Storage, Search, Cache, Email

  adapters:
    inbound_adapters: 6 routers + 1 main app
    outbound_adapters: 6 repository implementations + EventBus
    eventbus_adapter: Event publishing system

  di:
    composition_root: DIContainer pattern
    inversion_principle: Dependency flow diagram

  testing:
    pyramid: Unit → Integration → API → E2E
    test_organization: Folder structure

  error_mapping:
    404_not_found, 409_conflict, 422_unprocessable, 500_internal

  observability:
    structured_logging: 8 required fields
    tracing: request_id correlation

  performance:
    pagination: default 20, max 100
    query_optimization: 5 rules
    caching: 3 levels

hexagonal_conversion_status:
  step_1 through step_8:
    - Title, status, completion date
    - Files created
    - Deliverables
```

---

## 5. Cross-Reference Map

### When Rules Reference Each Other

**RULE-012 (Book soft delete)**
- ✅ Implementation details: DDD_RULES.yaml → domains.book.RULE-012
- ✅ Architecture pattern: HEXAGONAL_RULES.yaml → hexagonal.testing (mocks)
- ✅ Error handling: HEXAGONAL_RULES.yaml → error_mapping

**POLICY-003 (Bookshelf cascade)**
- ✅ Business logic: DDD_RULES.yaml → ddd.policies.POLICY-003
- ✅ Cross-domain effects: DDD_RULES.yaml → cross_domain_events.BookshelfDeleted
- ✅ EventBus implementation: HEXAGONAL_RULES.yaml → hexagonal.adapters.eventbus_adapter

**42 Endpoints**
- ✅ Complete list: HEXAGONAL_RULES.yaml → step_8.part_b_routers.endpoints_breakdown
- ✅ Domain mapping: DDD_RULES.yaml → domains.{module}.events (what each endpoint triggers)
- ✅ Error responses: HEXAGONAL_RULES.yaml → error_mapping

---

## 6. Why This Design?

### Problem Solved

| Original Issue | Solution |
|---|---|
| "God file" (3000+ lines) | Separated by concern (2483 + 1000+ lines) |
| Context-switching fatigue | Clear file naming: DDD vs Hexagonal |
| Hard to iterate | Experts can modify their domain independently |
| Single point of failure | Modular, can maintain each file separately |
| Search chaos | Predictable file structure + navigation guide |

### Design Principles Applied

1. **Single Responsibility**: Each file has one clear purpose
   - DDD_RULES: Business rules
   - HEXAGONAL_RULES: Architecture rules

2. **Separation of Concerns**: Business logic ≠ Infrastructure concerns

3. **Clean Architecture**: Domain stays independent from infra

4. **Maintainability**: Future developers can quickly find relevant documentation

---

## 7. Migration Path & Rollout

### Phase: Immediate (2025-11-13)

✅ **Complete:**
- DDD_RULES.yaml: 2483 lines (complete business rules)
- HEXAGONAL_RULES.yaml: 1000+ lines (complete architecture rules)

### Phase: Documentation

✅ **This ADR**: Explain three-file architecture

### Phase: Future

- If we add Chronicle/Search/Stats/Theme in Phase 2:
  - **DDD_RULES.yaml** grows (add new domains)
  - **HEXAGONAL_RULES.yaml** stays stable (no new architectural layers planned)

---

## 8. Related Decisions & ADRs

| ADR | Decision | Impact |
|-----|----------|--------|
| ADR-001 | Independent Aggregate Roots | Foundation for 6 modules |
| ADR-008-026 | Service & Repository designs | Detailed in DDD_RULES domains |
| ADR-027 | **This document** | Three-file separation |

---

## 9. Implementation Checklist

- [x] Extracted DDD_RULES.yaml (2483 lines, complete)
- [x] Created HEXAGONAL_RULES.yaml (1000+ lines, complete)
- [x] Documented file navigation in each file
- [x] Updated this ADR with cross-reference map
- [x] Verified no content loss
- [ ] Team training on new file structure
- [ ] Update wiki/onboarding docs with navigation guide
- [ ] Monitor for confusion in PR reviews (1-2 weeks)

---

## 10. References

**Primary Documents:**
- `backend/docs/DDD_RULES.yaml` - Business rules
- `backend/docs/HEXAGONAL_RULES.yaml` - Architecture rules

**Related ADRs:**
- ADR-001: Independent Aggregate Roots
- ADR-008: Library Service & Repository Design
- ADR-009: Bookshelf Service & Repository Design
- ADR-010: Book Service & Repository Design
- ADR-011: Block Service & Repository Design
- ADR-025: Tag Service & Repository Design
- ADR-026: Media Service & Repository Design

**Related Documents:**
- Phase 1.5 Integration Test Report (54 tests, 35% baseline)
- Hexagonal Conversion 8-Step Completion (2025-11-13)

---

## 11. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-13 | Merge DDD + Hexagonal into SYSTEM_RULES | Initial approach: single source of truth |
| 2025-11-13 | Discovered 3000+ line file challenges | Context-switching, navigation, maintenance issues |
| 2025-11-13 | Separated into three-file architecture | Clear separation of concerns, better maintainability |
| 2025-11-13 | **Accepted three-file design** | **THIS DECISION** |

---

## 12. Q&A

**Q: Why not one file with clear sections?**
A: Even with clear sections, 3000+ lines requires too much scrolling/searching. Separate files allow parallel editing and clearer mental models.

**Q: How do developers know which file to check?**
A: Navigation guide at top of each file + this ADR explains the strategy.

**Q: What if architecture changes?**
A: Only HEXAGONAL_RULES.yaml is modified. DDD_RULES.yaml remains stable (business doesn't change).

**Q: What if business rules change?**
A: Only DDD_RULES.yaml is modified. Architecture stays stable.

**Q: Will this become unmaintainable in Phase 2?**
A: No. Phase 2 (Chronicle, Search, Stats, Theme) only extends DDD_RULES with new domains. HEXAGONAL_RULES stays the same.

---

## 13. Success Criteria

- [x] All 26 DDD rules documented and accessible
- [x] All 14 business policies documented and accessible
- [x] All 10 domains with 5-layer implementation details documented
- [x] All architecture constraints (ports, adapters, DI, testing) documented
- [x] All 42 endpoints listed and categorized
- [x] All 27 events enumerated and traced
- [x] File navigation guide clear and complete
- [ ] No developer confusion in first week of using new structure
- [ ] Documentation review approved by team
- [ ] Wiki/onboarding updated

---

**Approved by:** Architecture Team
**Implementation Date:** 2025-11-13
**Status:** ACCEPTED ✅
