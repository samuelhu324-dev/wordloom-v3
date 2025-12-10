# ADR-062: Admin Route Mirror via Re-exports + Nested Dynamic Routes Mock Strategy

Date: 2025-11-16
Status: Proposed → Implemented (Nov 16, 2025)
Decision Type: Frontend Routing + Developer Experience

---

## Context

- Our App Router uses a route group `app/(admin)` which intentionally does not appear in the URL path.
- Product and docs require user-facing URLs under `/admin/...`.
- Nested dynamic routes for Library → Bookshelf → Book were needed immediately for demo and UI development, while backend data is not yet wired for those pages.
- We must minimize churn and keep a clear migration path to real API hooks.

## Decision

1. Expose `/admin/**` URLs by adding a mirror folder `app/admin/**` that re-exports components from `app/(admin)/**`.
   - Files are thin proxies like `export { default } from '@/app/(admin)/libraries/page';`.
   - This satisfies URL requirements with minimal duplication.
2. For three nested dynamic routes, use mock data during development:
   - `/admin/libraries/[libraryId]`
   - `/admin/libraries/[libraryId]/bookshelves/[bookshelfId]`
   - `/admin/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]`
   - Each page renders using local constants while `NEXT_PUBLIC_USE_MOCK=1` (feature flag planned).

## Alternatives Considered

- Migrate all files from `(admin)` to `admin/` now
  - Pros: No mirror; cleaner structure
  - Cons: Bigger change set; riskier under time pressure
- Configure `basePath` or rewrites in `next.config.js`
  - Pros: No mirror files
  - Cons: Alters all asset and link paths; added complexity
- Keep `(admin)` only
  - Cons: URLs would not include `/admin`, failing requirements

## Consequences

- Very small build impact: a handful of re-export modules only.
- Risk of drift between mirror and source is minimal because proxies have no logic.
- Clear path to remove proxies after full migration to `app/admin`.

## Implementation (Nov 16, 2025)

Created:
- `src/app/admin/layout.tsx`
- `src/app/admin/libraries/page.tsx`
- `src/app/admin/libraries/[libraryId]/page.tsx`
- `src/app/admin/libraries/[libraryId]/bookshelves/[bookshelfId]/page.tsx`
- `src/app/admin/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]/page.tsx`

Mock-enabled dynamic pages live under `(admin)`:
- `src/app/(admin)/libraries/[libraryId]/page.tsx`
- `src/app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/page.tsx`
- `src/app/(admin)/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]/page.tsx`

Supporting asset added:
- `src/app/(admin)/libraries/libraries.module.css`

## Migration Plan (Future)

- Phase A (now): Keep proxies, develop with mock data. Add `NEXT_PUBLIC_USE_MOCK` to switch to API hooks progressively.
- Phase B: When API integration is verified, migrate page sources from `(admin)` into `admin/` and remove proxies.
- Phase C: Delete mock blocks and toggle; keep a test fixture for Storybook/Playground only.

## Validation & Acceptance Criteria

- `/admin/libraries` renders without build errors (CSS module present).
- The three nested URLs render with mock data and BlockEditor visible on book page.
- Feature flag off (`NEXT_PUBLIC_USE_MOCK=0`): pages use hooks without runtime errors (post-integration).

## Rollback Plan

- Remove the `app/admin/**` mirror directory to revert to previous URLs (without `/admin`).
- Restore previous page versions from Git if needed.

## Risks & Mitigations

- Mirror drift: Keep proxies as single-line re-exports; no logic allowed.
- Inconsistent data source: Introduce explicit env flag `NEXT_PUBLIC_USE_MOCK` and log active source.
- URL confusion in tests: Add e2e smoke cases for the three URLs to CI.
