# Wordloom — Engineering Decision Index

This document summarises key engineering decisions made during the design and evolution of Wordloom, an internal, data-heavy knowledge management system.

## 1. Aggregation Boundary Design (DDD)
- Problem: Tight coupling across Library / Book / Block
- Decision: Split into multiple aggregates
- Trade-off: Increased coordination complexity

## 2. Delete vs Recycle Semantics
- Problem: Cascading delete risks
- Decision: Introduced recycle mechanism (Basement / Trash)
- Trade-off: Operational complexity

## 3. Schema Evolution & Migration Safety
- Problem: Frequent schema changes
- Decision: Alembic migrations + rollback-aware refactors
- Trade-off: Slower feature velocity

## 4. Admin vs Public Route Separation
- Problem: Diverging UI requirements
- Decision: Shared shell with route-level identity
- Trade-off: Early design overhead

## Decision: Delete vs Recycle Semantics

### Context
As relationships between Library, Book and Block deepened, hard deletes caused cascading data loss risks during schema changes.

### Constraints
- No backup infrastructure
- Frequent schema evolution
- Limited time for recovery

### Options Considered
1. Hard delete with foreign key constraints
2. Soft delete flags
3. Recycle-style logical deletion

### Decision
Chose a recycle-style mechanism (Basement / Trash) to separate logical deletion from physical cleanup.

### Trade-offs
- Added operational complexity
- Required additional cleanup logic

### Outcome
Significantly reduced risk during refactors and allowed safer experimentation with data models.
