# ADR-100: Bookshelf Book Gallery Strip (Plan64)

- Status: Accepted (Nov 27, 2025)
- Deciders: Wordloom Core Team
- Context: Bookshelf detail visual refresh, Plan64 execution, RULES synchronization
- Related: Plan_64_BookGallery.md, ADR-077 (Book Preview Cards), ADR-092 (Book Maturity Segmentation), ADR-094 (Bookshelf Dashboard), ADR-099 (Book Workspace Tabs)

## Context

Bookshelf detail pages currently render the book list as four maturity sections plus horizontal cards, which feels like a data table rather than a curated gallery. Product feedback and Plan64 require a "页面 → 陈列区模块 → 书架条 → 斜书" structure that instantly communicates "this shelf displays many books". The backend already exposes Book maturity counts through `useBooks` / `buildBookMaturitySnapshot`, and Phase 2 of Book Preview cards delivered horizontal scrolling plus 3D affordances. We need to compose those assets into a dedicated gallery strip while keeping the domain contract untouched.

## Decision

1. **Introduce Gallery Components**: Add `BookDisplayCabinet` (single tilted book) under `frontend/src/features/book/ui` and `BookshelfBooksSection` (header + strip) under `frontend/src/widgets/book`. `BookMainWidget` orchestrates them, feeding books + actions via props.
2. **UI-Only Curation**: The strip consumes existing `useBooks` output (seed + growing + stable by default), sorts locally by `updated_at`, and renders on a stylized shelf board. No domain fields such as `shelf_slot` or `display_angle` are added.
3. **Controls Stay Put**: The "该书架的书籍" heading, `+NEW BOOK` button, and inline creation form live inside the section header so that the strip and action panel feel contiguous. Mutations still call `useCreateBook`.
4. **Documentation Alignment**: `DDD_RULES.yaml`, `HEXAGONAL_RULES.yaml`, and `VISUAL_RULES.yaml` now describe the Book Gallery policy, adapter wiring, and visual guidelines to prevent regressions.

## Rationale

- Achieves the "作品展台" effect requested by stakeholders without touching backend APIs.
- Reuses existing hooks/components, minimizing implementation risk and avoiding duplicated data fetching.
- Keeps the maturity summary + sections available beneath the strip for detailed work flows while the top block focuses on perception.

## Scope

- Frontend files: `frontend/src/widgets/book/BookMainWidget.tsx`, `frontend/src/widgets/book/BookshelfBooksSection.tsx`, `frontend/src/widgets/book/BookshelfBooksSection.module.css`, `frontend/src/features/book/ui/BookDisplayCabinet.tsx`, `frontend/src/features/book/ui/BookDisplayCabinet.module.css`.
- Documentation: `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, this ADR.
- No backend or API contract changes.

## Non-Goals

- Introducing new book sorting APIs or curator metadata. The strip intentionally relies on client-side ordering.
- Replacing Book Maturity sections; they remain for operational context below the gallery.
- Shipping a brand-new cover generation pipeline; the component reuses existing cover URLs or default placeholders.

## Implementation Notes

- `BookDisplayCabinet` applies 3D transforms (`perspective(900px) rotateY(-18deg) rotateZ(-1deg)`), renders a spine and optional DRAFT badge, and forwards `onClick` to the parent.
- `BookshelfBooksSection` draws the radial-gradient background + wooden board, hosts the heading/actions slot, and ensures the strip is scrollable with keyboard support (tabindex + arrow navigation).
- `BookMainWidget` now composes: summaryBar → BookshelfBooksSection (with header + `+NEW BOOK` + inline form) → existing maturity sections (optional).
- Responsive rules shrink the cabinet from 140×200 (desktop) down to 110×160 (mobile) and reduce padding/gap while maintaining the board illusion.

## Testing

- Storybook stories for BookDisplayCabinet (single/variant) and BookshelfBooksSection (empty/one book/multi book) to lock the visuals.
- Vitest units verifying `activeBooks` aggregation (seed+growing+stable) and nth-child transform variations.
- Playwright path: open bookshelf detail → verify strip renders → click book navigates to `/admin/books/{bookId}` → create book via `+NEW BOOK` and ensure it appears on the strip.

## Rollback

Revert the new components and styles, restore the previous BookMainWidget header and BookPreviewList layout, and remove the added RULES + ADR entries. No schema migrations are involved.

## References

- `assets/docs/QuickLog/D39-45- WordloomDev/Plan_64_BookGallery_Implementation.md`
- `assets/docs/DDD_RULES.yaml`
- `assets/docs/HEXAGONAL_RULES.yaml`
- `assets/docs/VISUAL_RULES.yaml`
- `frontend/src/widgets/book/BookMainWidget.tsx`
- `frontend/src/features/book/model/api.ts`
