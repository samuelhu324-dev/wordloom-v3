# ADR-102: Book Tag Badge Pipeline

- Status: Accepted (Nov 26, 2025)
- Deciders: Wordloom Core Team
- Context: Plan_72_BookMaturityLevel.md (Stage 3), Book view-mode polish (ADR-101)
- Related: ADR-025 (Tag service), ADR-092 (Book maturity segmentation), ADR-100 (Book Gallery Strip), HEXAGONAL_RULES `book_tag_summary_adapter`, DDD_RULES `POLICY-BOOK-TAG-BADGE-SUMMARY`, VISUAL_RULES `book_gallery_visual_rules.tag_badges`

## Problem

Stage 3 of the Book widget overhaul introduces tag badges on both the showcase strip and row cards. The frontend already expects a `tagsSummary` array (`book.tagsSummary`) but the backend Book API never supplied tag names, forcing temporary fallbacks. We need an authoritative, bounded list of tag names per book without coupling the Book aggregate to the Tag aggregate.

## Decision

1. **Expose `tags_summary` on Book responses**: `BookResponse`, `BookDetailResponse`, and pagination payloads now include a `tags_summary: string[]` field (max 3 names, ordered by association time). Routers always return at least an empty array—never `null`.
2. **Batch-load tag names in the application layer**: `ListBooksUseCase` and `ListDeletedBooksUseCase` receive the shared AsyncSession from DI. After fetching books via `BookRepository`, they call `load_book_tags_summary(session, book_ids, per_book_limit=3)` to collect tag names from `tag_associations` + `tags` (EntityType=`book`).
3. **Keep the domain uncluttered**: The helper returns view-model data only; Domain `Book` stays unaware of tags. The DTO/response layer attaches the summary, satisfying UI needs without cross-bounded-context entanglement.
4. **Document & cap the contract**: RULES files capture the new behavior and the hard 3-tag limit. Any feature needing the full tag list must call the Tag module ports instead of hijacking this summary.
5. **Unify showcase/list interactions**: BookFlatCard and BookRowCard now render icon-only hover actions (view/edit/delete/pin) plus a silk-blue pin ribbon. The new Book edit dialog reuses the Bookshelf Tag UX and coordinates with Tag associate/disassociate endpoints, ensuring Book-level tag edits stay within the Tag bounded context.

## Consequences

- Positive: Gallery and list views finally reflect the same badge + hover affordances, making pinned books easy to scan. Sharing the Bookshelf dialog avoids a second form and guarantees all tag mutations still flow through Tag use-cases.
- Negative: Overlaying icon-only controls increases keyboard-focus requirements; we mitigated this with `opacity` transitions and `aria-label`s but need to keep regression tests around focus handling. Tag association/disassociation adds extra network hops per save—acceptable today but worth monitoring once libraries scale.

## Rationale

- A tiny summary array is sufficient for badges and prevents over-fetching entire tag metadata for every card.
- Reusing the existing AsyncSession avoids new repositories or N+1 TagRepository calls; a single query per list request keeps performance predictable.
- Keeping the Domain model clean maintains the Hexagonal boundary: only the application adapter understands how to project additional read-model data.
- The 3-item cap guarantees stable UI layout (badges wrap predictably) and aligns with Plan_72 messaging.

## Implementation Notes

- New helper `api/app/modules/book/application/tag_summary_loader.py` encapsulates the SQL join and ordering logic. It filters deleted tags and enforces the per-book cap inline.
- DI containers now pass the AsyncSession into `ListBooksUseCase` / `ListDeletedBooksUseCase`. Other callers can omit the session (the helper gracefully skips work).
- Router `_serialize_book` mirrors the new contract so single-book endpoints always include `tags_summary` (empty when not resolved).
- Frontend already maps `tags_summary` → `book.tagsSummary`, so no UI changes were required once the backend field appeared.

## Verification

1. `GET /api/v1/books?bookshelf_id=...` responses now show `tags_summary` arrays alongside maturity/status data; BookRowCard badges light up without fallback logic.
2. `GET /api/v1/books/deleted` returns the same field, allowing Basement lists to stay consistent.
3. Existing Create/Update endpoints continue returning empty arrays, satisfying the contract without extra queries.

## Future Work

- Extend `GetBookUseCase` to reuse the helper so the Book workspace header can display badges without a separate Tag fetch.
- Consider exposing tag IDs alongside names if later UX requires color chips; that would require a richer summary DTO and another ADR.
- Evaluate caching or batching strategies if Book edit tagging starts to stress the associate/disassociate endpoints, especially when multiple tags change per save.
