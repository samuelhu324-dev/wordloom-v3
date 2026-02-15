---
id: adr-003-checkpoint-marker-media-list-governance (Ordered + Dedup)
title: Bookshelf Overview
status: draft
date: 2025-01-20
related:
  - ck: 
  - spec: 
---

## Context
We store images in `media_resources` with soft-delete (`deleted_at`).
Recent investigation shows classic legacy data issues:
- Same `file_hash` appears multiple times (n>1), with multiple `entity_id` and multiple `file_path`.
- Repeated inserts for the same entity occur due to retries / lack of idempotency.
- Soft-deleted rows accumulate and the system lacks a clear “active record” rule.
- CHECKPOINT_MARKER supports multiple images, but the database model has no explicit ordering field,
  so the “list semantics” are implicit and unstable.

Evidence (SQL snapshots):
- Duplicated hashes: `file_hash -> count(paths, entities)`
- Soft-delete distribution: `alive vs soft_deleted`
- Entity distribution: only `CHECKPOINT_MARKER` in current sample

## Decision
We apply a **minimal stopgap** to prevent further data corruption, while keeping ordering work for later.

Rules (active rows only, where `deleted_at is null`):
1) A checkpoint marker may contain multiple images.
2) Re-uploading the same image (same `file_hash`) within the same marker **does not create a new active record**.
3) Enforce invariants using **partial unique indexes**:
   - Unique active `file_path`: `(file_path)` where `deleted_at is null`
   - Unique active hash per entity: `(workspace_id, entity_type, entity_id, file_hash)` where `deleted_at is null`

Out of scope (for this stopgap):
- Stable list ordering (`display_order`) and “ordered collection semantics”.

Write path expectation:
- Insert should be idempotent by `(workspace_id, entity_type, entity_id, file_hash)`; on conflict, return the existing active row.

## Consequences
Positive:
- Prevents “duplicate active” images and stops data from getting worse.
- Adds hard guardrails at the database level to force idempotency.
- Makes future cleanup / migration feasible (clear invariants).

Trade-offs / Risks:
- Existing dirty data may violate the new constraints; a cleanup pass is required before creating indexes.
- Ordering remains implicit/unstable until we introduce `display_order` and update reads.
- Write path must handle unique conflicts gracefully (return existing row instead of crashing).

## Implementation Plan
1) Run healthcheck queries to quantify duplicates and soft-delete distribution.
2) Cleanup (one-off):
   - For duplicated active `file_path`, keep the latest active row; soft-delete others.
   - For duplicated active `(workspace_id, entity_type, entity_id, file_hash)`, keep the latest active row; soft-delete others.
3) Create partial unique indexes for active rows.
4) Update write path to be idempotent:
   - Prefer “get-or-create” semantics for `(workspace_id, entity_type, entity_id, file_hash)`.
   - On unique conflict, return the existing active record.
5) (Follow-up) Add stable ordering: add `display_order`, backfill, and enforce ordering constraints.

## Rollback
- Drop the new indexes
- Keep `display_order` column (or drop if safe)
- Revert write path to previous behavior
- Disable new API via feature flag if applicable

## References
- DEV_LOG / investigation notes
- SQL healthcheck queries
- PR links / migration ID

## Implementation Evidence
- Healthcheck + cleanup + index DDL are captured in `backend/storage/assets/checklist/Before-After-SQL/healthcheck_media_resource.sql`.
- Cleanup transaction example (file_path duplicates): section **L** (begin/update/verify/commit).
- Guardrail indexes:
   - `uq_media_filepath_alive`: section **M**
   - `uq_media_entity_hash_alive`: section **N**
- Post-apply verification:
   - Duplicated active `(entity, hash)`: section **C** (expects 0 rows)
   - Duplicated active `file_path`: section **J** (expects 0 rows)
   - Confirm indexes exist: section **O** (pg_indexes)