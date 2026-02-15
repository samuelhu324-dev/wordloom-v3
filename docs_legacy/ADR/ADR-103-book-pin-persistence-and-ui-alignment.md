# ADR-103: Book Pin Persistence and UI Alignment

- Status: Accepted (Nov 27, 2025)
- Deciders: Wordloom Core Team
- Context: Book dashboard polish iteration (Nov 26–27), follow-up to ADR-100 (Book Gallery Strip) and ADR-102 (Tag Badge Pipeline)
- Related: DDD_RULES `POLICY-BOOK-PINNED-DISPLAY`, HEXAGONAL_RULES `book_view_modes_adapter`, VISUAL_RULES `book_gallery_visual_rules`, ADR-088 (Library Creation Dialog V2)

## Problem

The late-November polish pass exposed several regressions around book management:

- Pinning a book from the hover menu triggered the PATCH endpoint but `UpdateBookUseCase` ignored the `is_pinned` payload, so the repository persisted `false` and the UI reverted on refresh.
- Modal layouts drifted from the agreed pattern: extra heading spacing in shared modals and footer cancel buttons conflicted with the new strict-close requirement (close icon + success action only).
- The book hover menu was still positioned inside the card container, causing clipping under overflow contexts, and the bookmark glyph no longer matched the visual spec (star badge for pinned books).

## Decision

1. **Persist pin state in the application layer**: The domain `Book` aggregate gains `set_pinned(normalized_bool)` to update `is_pinned` and timestamps. `UpdateBookUseCase` now checks `request.is_pinned` and calls the setter before saving, reusing the existing repository mapping.
2. **Normalize modal contracts**: Shared dialogs (`BookEditDialog`, `BookshelfTagEditDialog`, `LibraryForm`) strip the footer cancel button, rely on the top-right close icon, and tighten the title/subtitle gap to 0 using the modal stylesheet override.
3. **Harden the hover menu UI**: `BookFlatCard` renders its quick menu through `createPortal` to `document.body`, preventing overflow clipping, and replaces the legacy pin icon with the Lucide star (outlined vs filled) while keeping the silk-blue ribbon for pinned books.
4. **Sync rule books**: Updated DDD/Hexagonal/Visual RULES to capture the pin workflow (application layer persistence) and the revised dialog/hover specifications, avoiding future drift between code and governance docs.

## Consequences

- Positive: Pin/unpin finally survives refresh and downstream analytics; UI affordances now match the silk-blue star guideline and modals behave consistently across the dashboard.
- Positive: Rule files now document the authoritative pattern, reducing future ambiguity for contributors.
- Negative: The domain still emits no dedicated "pinned" event; if other bounded contexts need pin notifications we must extend the aggregate later.
- Negative: Portal-based menus require extra attention to focus trapping and cleanup; tests must keep covering keyboard focus.

## Implementation Notes

- Backend: `backend/api/app/modules/book/domain/book.py` adds `set_pinned`; `UpdateBookUseCase` applies it when `is_pinned` is present.
- Frontend: `frontend/src/features/book/ui/BookFlatCard.tsx` updates hover menu positioning, icon assets, and aria state; associated CSS tightens the portal style.
- Book maturity snapshots sort pinned books first (most recent `updated_at` → oldest), mirroring the Bookshelf dashboard ordering contract.
- Shared modal CSS (`frontend/src/shared/ui/Modal.module.css`) forces zero gap; dialog components drop cancel buttons and rely on the close icon with backdrop lock.
- Documentation: DDD/Hexagonal/Visual RULES append the new guardrails, and ADR-103 records the rationale.

## Verification

1. Trigger `PATCH /api/v1/books/{id}` with `{ "is_pinned": true }` via the UI; verify the response echoes `is_pinned: true` and the database row updates accordingly.
2. Reload the Bookshelf dashboard; pinned books stay in the pinned segment with filled star icons and the silk-blue ribbon.
3. Open Book Edit / Bookshelf Tag / Library Creation dialogs; titles sit flush with content, only the primary action remains in the footer, and the close icon handles cancellation.
4. Hover over BookFlatCard cards in both gallery and row views; the portal menu appears above other layers without clipping, and keyboard focus moves correctly between icons.

## Future Work

- Consider emitting a dedicated `BookPinnedStateChanged` domain event if other modules need to react to pin transitions.
- Evaluate extracting a shared portal menu hook for other card grids to avoid duplicate positioning logic.
- Expand automated tests to cover the portal hover menu and modal close-only pattern (Playwright regression suite).
