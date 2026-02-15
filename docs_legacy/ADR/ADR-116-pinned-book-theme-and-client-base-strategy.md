# ADR-116: Book Pin Visual Sync & API Client Base Strategy

- Status: Accepted (Nov 29, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-094 (Library → Bookshelf theme integration), ADR-103 (Book pin persistence), ADR-115 (Theme propagation & manual verification), ADR-063 (Same-origin proxy), VISUAL_RULES `book_pin_visuals_v2`
- Related Artifacts: `frontend/src/features/book/ui/BookFlatCard.tsx`, `frontend/src/features/book/model/hooks.ts`, `frontend/src/shared/api/client.ts`, `frontend/manual-checks/libraryThemeManualCheck.ts`

## Problem

1. Book pin ribbons/badges were still hardcoding neutral gradients, so even after ADR-115 the Library accent color stopped at the card wall—the pin indicators looked out-of-sync and failed dark theme contrast checks.
2. The `useToggleBookPin` hook performed pessimistic updates only. Users clicked "Pin" and waited for a server round-trip before ribbon/badge state changed, leading to double-clicks, duplicate toasts, and stale pinned sections.
3. The shared API client still defaulted to an absolute `http://localhost:30001` base. In the browser this bypassed the Next.js dev proxy, triggering `CORS` failures for cover uploads and blocking QA flows whenever the backend ran on a different host.

## Decision

1. **Pin visuals consume theme tokens.** BookFlatCard now derives pin ribbon gradients and badge foreground/background colors from the `getBookTheme` accent, exposing them as CSS variables (`--book-flat-pin-start/end`, `--book-pin-badge-bg/fg`). Any Book UI that shows pin state must reuse these variables—no inline hex or detached gradients.
2. **Pin toggles are optimistic.** `useToggleBookPin` writes to the TanStack Query cache before awaiting the API response, using shared helpers to update both the bookshelf list cache and the pinned segment ordering. Failures roll back the cached snapshot and notify the user via toast, ensuring state never drifts silently.
3. **API base is relative-first.** `frontend/src/shared/api/client.ts` now resolves the base URL at runtime: when `window` exists it uses relative paths (leveraging Next dev proxy); only CI/Storybook set `NEXT_PUBLIC_API_BASE_URL` to override. This eliminates accidental cross-origin requests and keeps cover uploads within the same origin session.
4. **Rules stay synchronized.** VISUAL_RULES, DDD_RULES, and HEXAGONAL_RULES all reference the new pin/theme pipeline, the optimistic mutation contract, and the API base guardrails so future regressions must update governance documents alongside code.

## Consequences

- **Positive:** Pin ribbons and badges now inherit Library accents automatically, maintaining contrast guarantees established in ADR-094/115 while keeping UI tokens centralized.
- **Positive:** Optimistic pin toggles deliver instant feedback, reduce double-submits, and codify cache helpers for future bookshelf mutations.
- **Positive:** Relative API bases remove CORS headaches for uploads and keep dev/prod pointing at the same reverse proxy story.
- **Negative:** Cache helpers introduce extra maintenance overhead—any new book list query must plug into the shared mutation pipeline to remain consistent.
- **Negative:** Enforcing relative-first API calls means deploy scripts must explicitly set `NEXT_PUBLIC_API_BASE_URL` when bypassing the Next proxy (e.g., static exports), but the safety wins outweigh the configuration cost.

## Implementation Notes

1. **Frontend UI:**
   - `BookFlatCard.module.css` defines the new CSS variables and applies them to ribbon/badge gradients; any future Book card variant should import the same variables rather than duplicating styles.
   - Components obtain theme data via `getBookTheme` and pass `theme.pinAccent` to the CSS variables alongside existing wall/accent tokens.
2. **Frontend Hooks:**
   - `frontend/src/features/book/model/hooks.ts` exports `useToggleBookPin` with optimistic updates, rollback, and toast reporting; integration tests should mock the cache helpers to ensure they receive the correct Book IDs and bookshelf scopes.
   - Cache helpers live in the same module to keep mutation + query alignment explicit.
3. **API Client:**
   - `frontend/src/shared/api/client.ts` computes `baseURL` using `window?.location.origin` when available; the override env var is respected only when defined. All fetch callers must import this client instead of invoking `fetch` with hard-coded hosts (reinforced by the `no-raw-fetch-host` ESLint rule).
   - Cover upload troubleshooting steps in VISUAL_RULES now reference this ADR to flag any future regressions.
4. **Documentation & Verification:**
   - VISUAL_RULES documents the CSS variable contract and testing checklist (pin badge contrast, theme script run).
   - DDD_RULES codifies the manual theme check command plus the requirement that pin visuals stay in sync with library themes.
   - HEXAGONAL_RULES records the optimistic mutation behavior, cache key expectations, and API base fallback order. Any future adjustments must update all three files and reference ADR-116 in commit messages.
