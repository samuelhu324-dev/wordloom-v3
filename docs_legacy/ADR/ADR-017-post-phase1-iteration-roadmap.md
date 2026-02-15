# ADR-017: Post-Phase 1 Iteration Roadmap

**Status**: ACCEPTED
**Date**: November 12, 2025
**Context**: PHASE 1 completion with 100% test pass rate (23/23), now identifying next iteration priorities
**Participants**: Architecture Team
**Supersedes**: None
**Supplements**: ADR-016 (Round-Trip Integration Testing)

---

## Overview

After successful completion of PHASE 1 with **23/23 tests passing (100%)**, we have identified 4 high-priority improvements for the next iteration cycle. This ADR documents the roadmap, priorities, and implementation strategy.

### Current State Summary

```
✅ PHASE 1 COMPLETE
- All 4 domains implemented (Library, Bookshelf, Book, Block)
- Round-trip integration testing validated
- 100% test pass rate (23 tests, 260ms execution)
- No database I/O required (mock-based testing)
```

---

## Problem Statement

While PHASE 1 is successful, several improvements are now feasible and beneficial:

1. **Deprecation Warnings**: datetime.utcnow() deprecated in Python 3.14
2. **Test Coverage Gaps**: No database-level integration tests yet (all mock-based)
3. **Documentation Gaps**: Need to document tested behaviors for reference
4. **Performance Baseline**: Should establish metrics to prevent regressions

### Impact of Not Addressing

- Python 3.14+ will produce warnings (noise in CI/CD)
- Database migrations might have hidden issues
- Missing database-level constraint validation
- No baseline for performance optimization

---

## Solution: Post-Phase 1 Iteration Roadmap

### Priority 1: Fix Deprecation Warnings (Low Effort, High Impact)

**Objective**: Eliminate Python 3.14 deprecation warnings from test output

**Tasks**:
1. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` across all domains
2. Add `from datetime import timezone` to affected files
3. Verify test warnings reduced to 0

**Affected Files**:
- ✅ `backend/api/app/modules/domains/library/domain.py` - DONE
- ⏳ `backend/api/app/modules/domains/bookshelf/domain.py`
- ⏳ `backend/api/app/modules/domains/book/domain.py`
- ⏳ `backend/api/app/modules/domains/block/domain.py`

**Estimated Effort**: 30 minutes (4 files × 5 min each)

**Expected Outcome**:
```
Before: 80 deprecation warnings
After:  0 deprecation warnings
```

**Success Criteria**:
- ✅ Test execution output shows 0 warnings
- ✅ All 23 tests still pass

---

### Priority 2: Database Integration Tests (Medium Effort, Medium Impact)

**Objective**: Validate domain models work with actual database persistence layer

**Tasks**:
1. Create `test_*_database_integration.py` test files for each domain
2. Implement database fixtures (PostgreSQL/SQLite test DB)
3. Test CRUD operations at database level
4. Verify foreign key constraints enforced
5. Test cascade operations (delete, soft delete)

**Affected Domains**:
- Library
- Bookshelf
- Book
- Block

**Test Structure**:
```python
# Example: test_library_database_integration.py
@pytest.fixture
async def test_db():
    # Create test database
    # Run migrations
    # Yield connection
    # Cleanup after test

async def test_library_persistence():
    """Verify Library can be saved and retrieved from database"""
    # Create Library
    # Save to DB
    # Query from DB
    # Assert equality

async def test_cascade_delete():
    """Verify cascade rules work at database level"""
    # Create hierarchy
    # Delete parent
    # Verify children deleted/moved appropriately
```

**Estimated Effort**: 2-3 hours (per domain)

**Expected Outcome**:
- Database-level integration tests running
- Verified cascade behavior
- Confidence in ORM/database layer

**Success Criteria**:
- ✅ Each domain has ≥5 database integration tests
- ✅ All tests pass with real database
- ✅ Coverage for cascade operations

---

### Priority 3: Add Performance Baselines (Low Effort, Medium Impact)

**Objective**: Establish performance metrics to prevent regressions

**Tasks**:
1. Add `@pytest.mark.benchmark` to key tests
2. Record execution time baselines
3. Set performance thresholds in CI/CD
4. Alert on regressions

**Baseline Data**:
```
Current Performance (23 tests, all mocks):
- Total time: 0.26 seconds
- Average per test: 11.3 milliseconds
- Fastest: 1ms
- Slowest: 30ms (complex hierarchy setup)

Target Performance:
- Full test suite: < 1 second
- Average per test: < 50ms
- No test should exceed 100ms
```

**Tools**:
- pytest-benchmark plugin
- GitHub Actions performance tracking

**Estimated Effort**: 1 hour

**Expected Outcome**:
- Performance data tracked over time
- CI/CD alerts on regressions
- Baseline established for optimization

---

### Priority 4: Domain-Specific Documentation (Low Effort, High Value)

**Objective**: Document each domain's tested behaviors and expectations

**Tasks**:
1. Create `DOMAIN_TESTING_GUIDE.md` for each domain
2. Document:
   - Invariants being tested
   - Expected event sequences
   - Valid state transitions
   - Error cases and exceptions
3. Link from ADR documents
4. Keep in sync with tests

**Example Structure**:
```markdown
# Library Domain Testing Guide

## Tested Invariants
- RULE-001: Each user has exactly one Library
- RULE-002: Library must have user_id
- RULE-003: Library name must be 1-255 characters

## Expected Events
- LibraryCreated: Emitted on creation
- LibraryRenamed: Emitted on name change
- LibraryDeleted: Emitted on deletion
- BasementCreated: Auto-emitted with LibraryCreated

## State Transitions
- New → Active → Archived → Deleted (one direction)

## Test Coverage
- test_library_create: ✅ 4 assertions
- test_library_update: ✅ 3 assertions
- ... etc
```

**Estimated Effort**: 2-3 hours (all domains)

**Expected Outcome**:
- Clear reference for developers
- Documented test coverage
- Easier onboarding for new team members

---

## Implementation Timeline

### Week 1 (Nov 13-17)
- ✅ Priority 1: Fix deprecation warnings (30 min)
- ✅ Priority 3: Add performance baselines (1 hour)
- **Effort**: ~1.5 hours
- **Expected Outcome**: Clean CI/CD, performance tracking enabled

### Week 2 (Nov 20-24)
- ✅ Priority 2: Database integration tests (2-3 hours)
  - Library DB tests
  - Bookshelf DB tests
- **Effort**: ~3 hours
- **Expected Outcome**: Database layer validated for 2/4 domains

### Week 3 (Nov 27-Dec 1)
- ✅ Priority 2 (continued): Complete remaining DB tests
  - Book DB tests
  - Block DB tests
- ✅ Priority 4: Domain testing guides
- **Effort**: ~4-5 hours
- **Expected Outcome**: Full database integration coverage + documentation

---

## Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Test Pass Rate | 100% (23/23) | 100% (30+/30+) | Week 3 |
| Deprecation Warnings | 80 | 0 | Week 1 |
| Database Tests | 0 | ≥20 | Week 3 |
| Documentation Coverage | 40% | 100% | Week 3 |
| Test Execution Time | 0.26s | < 1.0s (w/ DB tests) | Week 3 |

---

## Risk Assessment

### Low Risk
- ✅ Deprecation fixes (isolated changes)
- ✅ Performance baselines (observation only)

### Medium Risk
- ⚠️ Database integration tests (requires test DB setup)
  - Mitigation: Use SQLite for simplicity
  - Isolation: Separate test database per test

### No Known High-Risk Items

---

## Decision Records

### Why These Priorities?

1. **Deprecation Warnings**: Python 3.14 is current, must fix before breaking
2. **Database Tests**: Only way to validate constraints (foreign keys, cascades)
3. **Performance**: Better to establish baseline now vs. optimizing later
4. **Documentation**: Developers need reference, reduces onboarding time

### Why Not Database Tests First?

- Mocks are sufficient for domain logic validation
- Database tests are integration-level, not unit-level
- Better to validate domain layer first, then add DB layer

### Why Include Documentation?

- Code is tested but behaviors not documented
- Developers might not understand all invariants
- Low effort, high value for long-term maintenance

---

## References

- **Current Test File**: `backend/api/app/tests/test_library/test_integration_round_trip.py`
- **Previous ADR**: ADR-016 (Round-Trip Integration Testing)
- **DDD Rules**: `backend/docs/DDD_RULES.yaml`
- **Python 3.14 Changes**: https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow

---

## Appendix: Code Examples

### Example 1: Deprecation Fix

```python
# BEFORE
from datetime import datetime
now = datetime.utcnow()

# AFTER
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### Example 2: Database Integration Test

```python
@pytest.mark.asyncio
async def test_library_database_persistence(test_db):
    """Verify Library persists and retrieves correctly"""
    # Arrange
    user_id = uuid4()
    library = Library.create(user_id=user_id, name="Test")

    # Act - Save to database
    repository = LibraryRepository(test_db)
    await repository.save(library)

    # Assert - Retrieve from database
    retrieved = await repository.get_by_id(library.id)
    assert retrieved.name.value == "Test"
    assert retrieved.user_id == user_id
```

### Example 3: Performance Baseline

```python
import pytest

@pytest.mark.benchmark
def test_library_creation_performance(benchmark):
    """Ensure library creation stays fast"""
    user_id = uuid4()

    result = benchmark(Library.create, user_id=user_id, name="Test")

    # Baseline: should complete in < 5ms
    assert result.id is not None
```

---

## Sign-Off

- **Decision**: ACCEPTED
- **Date**: November 12, 2025
- **Status**: READY FOR IMPLEMENTATION
- **Approved by**: Architecture Team
- **Next Review**: December 1, 2025 (post-iteration completion)

