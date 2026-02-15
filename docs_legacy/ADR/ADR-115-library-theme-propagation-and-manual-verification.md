# ADR-115: Library Theme Propagation & Manual Verification

- Status: Accepted (Nov 29, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-056 (Theme strategy), ADR-087 (Library cover avatar), ADR-094 (Library → Bookshelf theme integration), VISUAL_RULES `book_maturity_view_v2` section
- Related Artifacts: frontend manual check `frontend/manual-checks/libraryThemeManualCheck.ts`, shared helper `frontend/src/shared/theme/theme-pure.ts`, Book UI components (`BookShowcaseItem.tsx`, `BookRowCard.tsx`, `BookFlatCard.tsx`, `BookPreviewCard.tsx`)

## Problem

1. Book cards inside Bookshelf Dashboard and the Book Preview list still default to the brown placeholder because the `library_theme_color` data path was optional and frequently omitted when books were fetched without their parent library context.
2. The theme helper (`getBookTheme`) already supports explicit colors, but the lack of contractual documentation let view components re-implement ad-hoc hashing, causing visual drift between the bookshelf wall gradient and individual book cards.
3. Manual testing instructions were missing, so regressions (e.g., dropping the color column in a serializer) went unnoticed until QA reported inconsistent palettes.

## Decision

1. **DTO propagation is mandatory.** All book read models that power UI lists (`GetBookshelfBooksUseCase`, `ListLibraryBooksUseCase`, `ListLibraryOverviewBooksUseCase`) must populate `BookDto.library_theme_color` by joining the owning library row. When the stored cover color is null, the DTO still carries the library identifier so `getBookTheme` can fall back to deterministic hashing.
2. **UI consumes a single source of truth.** Book cards (`BookShowcaseItem`, `BookRowCard`, `BookFlatCard`, `BookPreviewCard`) must call `getBookTheme({ coverColor: book.library_theme_color ?? null, libraryColorSeed: book.library_id ?? book.bookshelf_id ?? book.id })` and feed `theme.accentColor` into the CSS custom properties that paint gradients, walls, and glyph backplates. No component may re-hash colors or store `coverColor` in local state.
3. **Manual verification is codified.** The repository keeps `frontend/manual-checks/libraryThemeManualCheck.ts`, a TSX runner that logs the accent color for explicit color and fallback scenarios. Engineers run `npx tsx --tsconfig frontend/tsconfig.json frontend/manual-checks/libraryThemeManualCheck.ts` whenever they touch the theme pipeline to prove explicit color precedence (`coverColor → library_theme_color → libraryColorSeed`).
4. **Rules stay in sync.** VISUAL_RULES now documents the dependency on `getBookTheme` plus the manual check command so future UI/Theme changes must update both the helper and the governance file.

## Consequences

- **Positive:** Book cards inherit the same silk/ink palette as their parent library, fixing the brown wall regression and keeping bookshelf walls, preview strips, and dashboard rows visually coherent.
- **Positive:** Manual verification reduces guesswork—anyone can rerun the TSX script locally or in CI logs to confirm priority order without spinning up the full Next.js stack.
- **Negative:** Backend queries now JOIN libraries to pull `library_theme_color`, adding minimal overhead; caching layers must be aware of the new column.
- **Negative:** The manual check becomes an extra step during theme-related PRs, but it is lightweight and scripts already live in the repo.

## Implementation Notes

1. **Backend:**
   - Update book assemblers/DTO factories so `library_theme_color` is always present; add regression tests ensuring bookshelf/list endpoints expose the field.
   - When a future migration introduces customizable book covers, keep `library_theme_color` as the default pipeline and only override when a book-level color is explicitly set.
2. **Frontend:**
   - Ensure every Book card component consumes `getBookTheme` (no inline hashing) and pipes `theme.accentColor` / `theme.glyph` into the existing CSS variables (`--book-card-accent`, `--book-card-glyph`).
   - Book cards must not attempt to read CSS variables from the DOM; the helper result is the contract.
3. **Testing & Docs:**
   - Add a manual checklist item referencing the TSX runner command; reviewers can paste the console output into PR comments when verifying a theme-related change.
   - Keep VISUAL_RULES / DDD_RULES updates in lock-step with this ADR; any change to the color precedence order must revise all three artifacts and link back here.
