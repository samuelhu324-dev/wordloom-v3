# ADR-101: Book View Modes (Showcase + Row)

- Status: Accepted (Nov 26, 2025)
- Deciders: Wordloom Core Team
- Context: Plan_67_BookView.md, gallery shrink feedback (Plan64→66), documentation alignment request
- Related: ADR-092 (Book Maturity Segmentation), ADR-099 (Book Workspace Tabs), ADR-100 (Book Gallery Strip), VISUAL_RULES.yml `book_view_modes`, DDD_RULES.yml `POLICY-BOOK-VIEW-MODES`, HEXAGONAL_RULES.yml `book_view_modes_adapter`

## Context

Book pages currently only expose the Plan64 “展柜 Strip” layout. Stakeholders now require two complementary modes: (A) showcase mode to appreciate curation and (C) row mode to scan/manage dense metadata. The team also wants a single 3D book primitive so that both modes stay visually consistent and easier to maintain. Domain contracts remain unchanged (BookDto already exposes title/summary/status/maturity/block_count/updated_at), so the entire effort lives in the presentation adapter + RULES/ADR updates.

## Decision

1. **Extract Book3D**: Move the tilted-book DOM + CSS from `BookDisplayCabinet` into `Book3D` (`frontend/src/features/book/ui/Book3D.tsx/.module.css`). The component accepts `BookDto` plus overrides (glyph/status/accent/size) and exposes two sizes (`showcase`, `compact`).
2. **Define Two Wrappers**:
   - `BookShowcaseItem` (alias `BookDisplayCabinet`) = Book3D (showcase) + plaque (title + maturity pill + blocks + relative time).
   - `BookRowCard` = Book3D (compact, no hover overlay) on the left, info stack on the right (title, summary, block count, updated time, optional tags).
3. **Add View Mode Toggle**: `BookMainWidget` now keeps `viewMode: "showcase" | "row"` state and renders either `BookshelfBooksSection` (A-mode) or a column of `BookRowCard`s (C-mode) per maturity section. A two-button segmented control (`aria-pressed`) in the header lets users switch modes.
4. **Sync RULES + ADR**: VISUAL/DDD/HEX files describe the new view modes, the shared Book3D policy, and the fact that view preferences remain client-side. This ADR documents the architectural intent.

## Rationale

- Showcase vs row address different user mindsets (欣赏 vs 管理) without duplicating data fetching.
- A single Book3D component prevents divergence between strip cards, preview cards, and any future list/layout variants.
- Keeping the toggle + rendering logic inside existing Book widgets minimizes routing or backend impact, meeting the “UI-only change” constraint from DDD/HEX rules.

## Scope

- Frontend: `frontend/src/features/book/ui/Book3D.tsx/.module.css`, `BookShowcaseItem.tsx`, `BookRowCard.tsx/.module.css`, `bookVisuals.ts`, `frontend/src/widgets/book/BookMainWidget.tsx/.module.css` (toggle + row rendering), `BookDisplayCabinet.tsx` (re-export), callers (`BookPreviewCard`, `BookshelfBooksSection`) continue working via aliases.
- Documentation: `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, this ADR.
- No backend services, schemas, or ports.

## Non-Goals

- Persisting the user’s preferred view mode server-side. Future preference storage would require a dedicated Port + ADR.
- Replacing the maturity summary bar or removing the strip entirely; both modes coexist and are discoverable per section.
- Revisiting cover-generation logic or introducing new Book API fields.

## Implementation Notes

- `Book3D` centralizes placeholder glyphs, cover URLs, maturity color tokens, hover overlay, and badges. Size variants rely on `data-size` attributes.
- `BookShowcaseItem` wraps Book3D and reuses the existing plaque styles; `BookDisplayCabinet` simply re-exports it for backward compatibility.
- `BookRowCard` exposes keyboard-accessible cards (`role=button`, Enter/Space), keeping `onSelect` wiring identical to the strip.
- `BookMainWidget` injects the view toggle into the header actions row and branches the maturity-section body to `BookshelfBooksSection` or `.rowList` of `BookRowCard`s.

## Testing

- Manual: toggle between 展柜/条目, ensure selection still navigates to `/admin/books/{bookId}` in both modes, verify responsive breakpoints for compact 3D size.
- Storybook (to be added): Book3D (showcase/compact), BookRowCard, showcase strip with keyboard nav.
- Lint: `npm run lint` (frontend) to ensure new modules respect project rules.

## Rollback

Revert the new components and view-mode state, restore `BookDisplayCabinet`’s inline 3D DOM, delete `BookRowCard`, and remove the new RULES + ADR entries. Because no migrations or ports changed, rollback is limited to frontend + docs.

## References

- `assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_67_BookView.md`
- `assets/docs/VISUAL_RULES.yaml`
- `assets/docs/DDD_RULES.yaml`
- `assets/docs/HEXAGONAL_RULES.yaml`
- `frontend/src/widgets/book/BookMainWidget.tsx`
- `frontend/src/features/book/ui/Book3D.tsx`
