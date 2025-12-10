# ADR-104: Book Todo · Block Integration and Chronicle Timeline Linkage

- Status: Accepted (Nov 27, 2025)
- Deciders: Wordloom Core Team
- Context: Plan_76_BlockTypes++.md, Plan_42_BlockTypesNarrowingDown.md, Plan_72_BookMaturityLevel.md, ADR-092 (Book maturity), ADR-093 (Chronicle timeline), ADR-099 (Book workspace tabs)
- Related: DDD_RULES `POLICY-BLOCK-TODO-EMBEDDED-MODEL`, `POLICY-BOOK-TODO-PROJECTION`, `POLICY-CHRONICLE-TODO-MAPPING`, `POLICY-BOOK-MATURITY-TODO-GATE`; HEXAGONAL_RULES `todo_projection_strategy`, `block_todo_content_contract`, `no_nested_todo_endpoints_rule`; VISUAL_RULES `book_workspace_todo_visual_rules`, `block_todo_visual_rules`, `book_maturity_visual_rules`

## Problem

The Book workspace must surface actionable Todo information that originates inside Block content while keeping aggregates independent. Current Blocks only persist opaque JSON payloads; Book pages cannot reliably aggregate Todo counts, and Chronicle timelines lack visibility into Todo progress. The maturity score (seed/growing/stable) also ignores open tasks, producing misleading stability claims.

## Decision

1. **Keep Todo items embedded in Block content**: `block.content` continues to store `list_todo` payloads (`items[{id?, text, status=open|done, is_promoted?, priority?, due_date?}]`). Blocks remain the only aggregate that mutates Todo state; no `todo_items` table or repository is introduced.
2. **Define the core Block type set**: The canonical `block_kind` enumeration now includes `heading`, `paragraph`, `list_bullet`, `list_numbered`, `list_todo`, `code`, `callout`, `quote`, and `divider`. `custom`/`experimental` stays available for trials but cannot replace the core set. Phase 0 ships heading/paragraph/list_*, Phase 1 unlocks code/callout/quote/divider.
3. **Project Book-level Todo views without new write endpoints**: Stage 0 derives Book Todo badges, overview cards, and filters entirely on the frontend (`deriveBookTodosFromBlocks`). Stage 1 may optionally add `GET /api/v1/books/{book_id}/todos` backed by `ITodoProjectionQueryPort.list_book_todos(...)`, still following Pagination Contract V2. All Todo mutations continue to call Block use-cases.
4. **Extend Chronicle with Todo events**: Block diffing emits `TodoItemCreated/Completed/Reopened/Deleted` domain events. The Chronicle handler persists them as `todo_item_{created|completed|reopened|deleted}` and `GET /api/v1/chronicle/books/{id}/events` accepts `event_types[]=todo_item_*`. Timeline filters default to off to avoid noise but become user-toggleable.
5. **Link maturity scoring to Todo completion**: `BookMaturityScoreService` now allocates up to 20 points based on open Todo count (`open_todos = 0 → +20`, `open_todos ≥ 20 → +0`). When `maturity_score ≥ 70` yet `open_todos > 0`, the Book detail surfaces a warning; an optional feature flag can hard-block `STABLE` promotion until all Todo items are closed.
6. **Preserve flat routing boundaries**: No nested `/books/{id}/blocks/{blockId}/todos` routes are allowed. The optional read-only projection endpoint remains flat, and all write flows keep using the existing `/api/v1/blocks*` contracts.

## Consequences

- Positive: Book pages obtain consistent Todo counts, promoted-task views, and timeline history without introducing a new aggregate. Maturity badges now reflect incomplete work, reducing false "Stable" states.
- Positive: The Block editor gains a stable, documented `list_todo` behavior, unlocking later analytics on Callout/Todo metrics.
- Neutral: Diffing Block payloads adds modest application-layer complexity but avoids schema churn. The fallback hash for legacy Todo rows ensures Chronicle still logs events.
- Negative: Stage 0 projections can become heavy for books with hundreds of blocks. The optional projection port is reserved to relieve that pressure when needed.

## Rationale

- Embedding Todos inside Block content honors the independent aggregate design while aligning with Plan_42's explicit block types.
- A projection-first approach eliminates premature database migrations and lets the UI validate interactions before stabilizing an API.
- Chronicle is already the canonical audit log; extending it with Todo events keeps lifecycle, structure, and task progress in one stream.
- Maturity scoring must align with the operational definition of "Stable"—unfinished Todos represent real risk, so they penalize score automatically.
- Enforcing flat endpoints upholds previously accepted ADRs on independent aggregates and reduces cognitive load for future contributors.

## Implementation Notes

- `UpdateBlockUseCase` parses previous vs. next `list_todo` content, issuing domain events per state change. Items without IDs receive a derived key (`{block_id}:{index}:{sha1(text)}`) until the UI injects UUIDs on the next save.
- `BookMaturityScoreService` calculates base points (title/description/tag/block variety), block count points, and Todo deductions, exposing both the total score and a breakdown for UI badges.
- Frontend hooks: `useBookWorkspaceTodos` wraps TanStack Query cache; `deriveBookTodosFromBlocks` keeps the Stage 0 aggregation pure and memoized. Star icons toggle `is_promoted` via Block updates only.
- Timeline chips remember Todo filters in `localStorage('wordloom.book.timeline.todo_filter')`. When enabled, events reuse the existing pagination path without manual event injection.
- Policy and rule updates are synchronized across DDD/HEXAGONAL/VISUAL rulebooks to avoid drift. Basement/Legacy guards stay in place—Todo controls disable automatically under read-only conditions.

## Verification

1. Block mutations emitting Todo diffs populate Chronicle rows visible via `GET /api/v1/chronicle/books/{id}/events?event_types[]=todo_item_completed`.
2. Book detail overview shows accurate counts of promoted Todos, and the Blocks tab star/unstar flow only calls `/api/v1/blocks/{id}`.
3. The maturity badge warning appears when `maturity_score ≥ 70` but `open_todos > 0`, and disappears after completing outstanding tasks.
4. Contract tests confirm the optional `GET /api/v1/books/{id}/todos` (when enabled) returns Pagination V2 payloads and respects filters.
5. Snapshot and accessibility tests cover Todo badges, promoted lists, and read-only guardrails in the frontend scope.

## Future Work

- Implement the optional projection query port once Block counts per book routinely exceed Stage 0's comfortable threshold.
- Record Callout `warning/danger` blocks as Chronicle risk events, complementing Todo milestones.
- Expose maturity score breakdown via API response fields so analytics dashboards can visualize the contribution of each factor.
- Evaluate a debounce or CRDT-style diff for very large Todo lists if editing frequency increases.
