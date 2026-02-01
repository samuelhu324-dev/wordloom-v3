---
id: adr-004-blob-ref-minimal-stopgap
title: Media Storage Minimal Stopgap (Blob + Ref)
status: draft
date: 2026-01-21
related:
  - adr: adr-003-checkpoint-marker-media-list-governance (Ordered + Dedup)
---

## 0) Minimal Target (today == win)
Keep the upload entry usable, but make the write path **idempotent** and **recoverable**:
- Write **blob** first (content-addressed by `file_hash`)
- Then write **ref** (entity-addressed, points to blob)
- Upgrade “random tags / prints” into **eventified structured fields** (searchable + comparable)

Not doing today:
- Full historical data migration
- GC / reachability / lifecycle
- Full derived image pipeline (thumbnail variants, transforms)

## 1) ADR-mini (≤10 lines)
- Blob = unique binary addressed by `file_hash` (global uniqueness).
- Ref = `(workspace_id, entity_type, entity_id, role, position)` -> `blob_hash`.
- Active uniqueness (where `deleted_at is null`):
  - one active slot: `(workspace_id, entity_type, entity_id, role, position)`
  - no duplicate hash per entity-role: `(workspace_id, entity_type, entity_id, role, blob_hash)`
- Write: in a transaction, `upsert(blob by hash)` then `upsert(ref by entity slot / dedup by blob)`.
- Compatibility: keep legacy reads/writes working; allow dual-write during transition.

## Context
Current media writes are tightly coupled to entity rows (`media_resources`) and are subject to retries / non-idempotent behavior.
We need a minimal change that keeps the upload entry usable today, while making the write path idempotent and making future refactors cheaper.

Key idea (two-step write):
- First write **Blob** (content-addressed, keyed by `file_hash`) 
- Then write **Ref** (entity-addressed pointer that references a blob)

## Decision
We introduce two logical concepts (implemented as tables in the target design; stopgap can be dual-write / adapter-based):

### Blob
- Definition: a unique binary object addressed by `file_hash`.
- Invariant: `file_hash` is globally unique for blob.
- Minimal fields:
  - `file_hash` (PK or unique)
  - `content_type`, `size_bytes`
  - `storage_key` (or `file_path` if we keep filesystem-like layout)
  - `created_at`

### Ref
- Definition: an entity-scoped reference to a blob.
- Key (business slot): `(workspace_id, entity_type, entity_id, role, position)`.
- Points to: `blob_hash` (= `file_hash`).
- Invariants (active rows only, where `deleted_at is null`):
  - Unique active slot per entity: `(workspace_id, entity_type, entity_id, role, position)`
  - Unique active hash per entity+role: `(workspace_id, entity_type, entity_id, role, blob_hash)`
- Soft delete rule: deleting a ref does not delete the blob (GC is future work).

## Write Path (Minimal)
Within a transaction:
1) Compute `file_hash`.
2) Upsert blob by `file_hash` (no duplicate blobs).
3) Upsert ref by `(entity, role, position)` and/or dedup by `(entity, role, blob_hash)`.

Suggested conflict semantics (stopgap-friendly):
- If `(entity, role, blob_hash)` already exists and is active: return it (idempotent retry).
- Else if `(entity, role, position)` exists and is active: update slot to point to new blob (replace).
- Else: insert new ref.

Compatibility:
- Dual-write strategy (recommended for minimal risk):
  - Continue writing legacy `media_resources` (to keep existing reads stable)
  - Also write blob+ref for new path validation
  - Add a feature flag to switch reads to ref-based output later
- Read adapter options:
  - Service-layer adapter: map ref records back into the legacy response shape
  - SQL view (optional): `media_resources_compat_v` that joins refs -> blobs

## Consequences
- Upload is idempotent by hash.
- Entity duplication pressure moves from “binary storage” to “refs”, where constraints are clearer.
- Enables later GC / lifecycle management by blob reachability.

Risks / trade-offs:
- Requires careful transaction + conflict handling to avoid unique violations under concurrency.
- Dual-write increases complexity temporarily; needs clear cutover plan.
- Existing dirty legacy data remains; stopgap only ensures new writes do not worsen.

## Observability (Eventified Tags)
We standardize log/trace fields to replace ad-hoc tags/prints.

Required structured fields:
- `request_id` (or trace id)
- `operation_name` (stable business action name)
- `event` (stable event name)

Recommended fields for media:
- `workspace_id`, `entity_type`, `entity_id`
- `blob_hash`, `role`, `position`
- `dedup_hit` (boolean), `write_target` (`legacy|blob|ref|dual`)

Recommended event names (examples):
- `MEDIA_HASH_COMPUTED`
- `MEDIA_BLOB_UPSERTED`
- `MEDIA_REF_UPSERTED`
- `MEDIA_WRITE_DEDUP_HIT`
- `MEDIA_WRITE_CONFLICT_RETRY`

## Implementation Plan
1) Schema:
  - Create `media_blobs` (unique on `file_hash`).
  - Create `media_refs` (FK-like relationship to `media_blobs.file_hash` by convention).
2) Constraints:
  - Add partial unique indexes for active refs:
    - `(workspace_id, entity_type, entity_id, role, position)` where `deleted_at is null`
    - `(workspace_id, entity_type, entity_id, role, blob_hash)` where `deleted_at is null`
3) Write path:
  - Implement transactional upsert (blob -> ref).
  - Implement conflict semantics (dedup/retry-safe).
  - Emit eventified tags (above) at each decision point.
4) Rollout:
  - Enable dual-write first.
  - Add a short “healthcheck” job/dashboard: compare legacy vs ref counts and sample correctness.
  - Cut over reads behind a flag; keep rollback to legacy.
5) Follow-up:
  - Backfill refs for existing legacy rows.
  - Add GC/reachability for unreferenced blobs.

## Implementation Evidence
- Migrations:
  - `create table media_blobs ...`
  - `create table media_refs ...`
  - `create unique index ... where deleted_at is null`
- Verification SQL:
  - blob de-dup: `file_hash -> count(*)` should be 1
  - active ref uniqueness checks: group/having count(*) > 1 should return 0
- Runtime evidence:
  - log samples show `operation_name` + `event` + `request_id` + `dedup_hit`
- PR links / migration IDs: TBD
