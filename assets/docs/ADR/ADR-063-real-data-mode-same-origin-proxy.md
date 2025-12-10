# ADR-063: Switch to Real Data Mode via Same-Origin Proxy (30001)

Date: 2025-11-16
Status: Accepted (Nov 16, 2025)
Decision Type: Frontend Runtime & Integration

---

## Context
- ADR-062 introduced an admin route mirror and mock data to unblock UI.
- We now need to run with the real database/backend while keeping a seamless developer experience and stable URLs.
- Previous 404s occurred because frontend and backend shared the same port (30001), so API requests hit Next.js instead of the API server.

## Decision
- Fix the browser entrypoint at `http://localhost:30001` for the frontend (Next.js dev server).
- Run the backend on a separate port, default `http://localhost:30002`.
- Enable a same-origin proxy in `next.config.js` using Next Rewrites:
  - `source: /api/v1/:path* -> destination: http://localhost:30002/api/v1/:path*`
  - Both target host and prefix are configurable: `API_PROXY_TARGET`, `API_PROXY_PREFIX`.
- Disable mock mode by default: `NEXT_PUBLIC_USE_MOCK=0`.
- Keep the mock toggle as a fallback for Storybook/Playground only.

## Env & Configuration
- `.env.local` (frontend):
  - `NEXT_PUBLIC_USE_MOCK=0`
  - `NEXT_PUBLIC_API_BASE=http://localhost:30001` (same-origin base)
  - `API_PROXY_TARGET=http://localhost:30002`
  - `API_PROXY_PREFIX=/api/v1` (or `/api` to match backend)
- `src/shared/lib/config.ts` continues to use `config.api.prefix` set to `/api/v1`.

## Alternatives Considered
- CORS with absolute backend base URL
  - Works but requires cross-origin allowances; more friction during dev.
- Move all pages from `(admin)` to `admin/` immediately
  - Orthogonal; kept for future migration; mirror remains minimal.
- Keep mock mode
  - Not acceptable for integration testing with real DB.

## Consequences
- Browser always talks to the same origin (30001); no CORS issues.
- Backend port decoupled from frontend; no collisions.
- Simple rollback: set `NEXT_PUBLIC_USE_MOCK=1` and/or remove rewrites.

## Migration Plan
1. Start backend on 30002 and confirm `/health` and `openapi.json` reachable.
2. Update `.env.local` as above; restart Next dev server on 30001.
3. Validate routes:
   - `/admin/libraries`
   - `/admin/libraries/{libraryId}`
   - `/admin/libraries/{libraryId}/bookshelves/{bookshelfId}` and `/books/{bookId}`
4. If backend prefix differs, change `API_PROXY_PREFIX` to match, or add API alias on backend.

## Acceptance Criteria
- The three admin routes render using real data with mock disabled.
- Network requests `/api/v1/...` from the browser return 2xx via the proxy.
- Error/empty states render per VISUAL_RULES; not-found and error boundaries active.

## Rollback Plan
- Set `NEXT_PUBLIC_USE_MOCK=1` to re-enable mocks.
- Remove/disable rewrites in `next.config.js` if necessary.

## Related
- ADR-062: Admin Route Mirror & Mock Strategy
- VISUAL_RULES.yaml: Update runtime and environment sections to reflect same-origin proxy mode.
