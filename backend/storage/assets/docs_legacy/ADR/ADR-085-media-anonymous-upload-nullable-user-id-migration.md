# ADR-085: Media Anonymous Upload & Nullable user_id Migration

Status: Accepted
Date: 2025-11-22
Authors: Architecture / Infra Team
Related Artifacts: HEXAGONAL_RULES.yaml, VISUAL_RULES.yaml, DDD_RULES.yaml, Migration 016_allow_media_user_nullable.sql

## Context
Anonymous (unauthenticated or dev-mode) media uploads returned HTTP 500 because `media.user_id` was defined NOT NULL in both the ORM model and the domain aggregate. Early development runs with a single real user and historical media rows made synthetic assignment brittle. Upload use cases contained a hard-coded developer UUID fallback which diverged from existing data and obscured true ownership semantics.

## Problem
The NOT NULL constraint on `media.user_id` forced every upload to fabricate an owner. This caused:
- Runtime 500 errors when no authenticated user context existed.
- Pollution of ownership data with a stub UUID hindering later multi-tenant rollout.
- Increased branching logic in use cases (fallback user injection) and reduced clarity in repository filtering.

## Decision
1. Make domain aggregate `Media.user_id: Optional[UUID]`.
2. Alter ORM model column `user_id` to `nullable=True`.
3. Create and apply migration `016_allow_media_user_nullable.sql` dropping NOT NULL (executed Nov 22, 2025).
4. Remove developer fallback user assignment in `upload_image.py` & `upload_video.py`; pass through real `user_id` or `None`.
5. Expose repository listing without implicit user filtering while single-user mode is active (see ADR-082). Future multi-tenant will reintroduce scoped queries.

## Implementation Summary
- Domain: `media.py` updated (factory methods accept optional user_id).
- Infrastructure: `media_models.py` column changed to nullable, serialization tolerant of None.
- Application: Upload use cases simplified—no synthetic UUID injection.
- Migration: Added file `backend/api/app/migrations/016_allow_media_user_nullable.sql`; applied successfully. Legacy migrations `001` & `004` re-run failure acknowledged as expected (duplicate structures / conflicting NOT NULL during replay).
- Documentation: Rule files updated with status fields and new policy (POLICY-MEDIA-ANONYMOUS-UPLOAD).

## Consequences
Positive:
- Anonymous uploads persist without error.
- Data model aligns with current single-user + dev workflow.
- Clear path to later backfill ownership when multi-tenant mode activates.
Risks:
- Orphan (NULL user_id) rows could leak when user scoping introduced.
- Aggregated analytics per user must treat NULL separately.

## Mitigations & Future Work
- Introduce `backfill_owner_id` maintenance script before enabling multi-tenant.
- Add feature flag to toggle user-scoped filtering in media repository.
- When backfilling, record mapping audit trail (chronicle events) for compliance.
- UI: Display "匿名" badge for media without owner; do not fabricate UUID client-side.

## Alternatives Considered
- Retain NOT NULL and force a system user: Rejected (obscures real ownership, adds churn when true multi-user arrives).
- Separate AnonymousMedia table: Rejected (unnecessary complexity; introduces joins and dual repository maintenance).

## Decision Drivers
- Simplicity for current dev stage.
- Avoid dirty ownership data.
- Prepare for clean multi-tenant transition.

## Backout Plan
If unforeseen issues arise, revert domain/ORM changes and reapply NOT NULL with a bulk assignment script. Cost: medium (requires data scan + update). Current assessment: low probability.

## Verification
- Migration applied: successful log entry Nov 22, 2025.
- Test manual upload without user context: persisted row with NULL user_id.
- No further 500 errors from NOT NULL violation reproduced.

## References
- ADR-082 (Single-user library listing mode)
- HEXAGONAL_RULES: `media_user_nullable_decision`
- VISUAL_RULES: `media_upload_ui_strategy`
- DDD_RULES: `POLICY-MEDIA-ANONYMOUS-UPLOAD`
