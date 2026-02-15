# ADR-071: Multi-Library Support, Flat Endpoints, and Page Isolation

- Status: Accepted
- Date: 2025-11-18
- Authors: Wordloom Core
- Supersedes: implicit one-library-per-user guidance in earlier rules
- References:
  - DDD_RULES.yaml (updated)
  - HEXAGONAL_RULES.yaml (updated)
  - VISUAL_RULES.yaml (updated)
  - 3_CoreModulesUI.md (UI authority)
  - 4_IndependentAggregateRoots.md (Aggregate independence)

## Context

Historically, the system assumed a strict 1:1 relationship between User and Library (RULE-001) and contained several examples of nested backend routes. The current product direction requires:
- Multiple libraries per user (no hard limit)
- Strict independent aggregate roots (Library, Bookshelf, Book, Block)
- Flat backend routes with query filters (no nested backend routing)
- Page isolation: each page shows only its own entity
- Block is not a standalone page (edited within Book)

## Decision

1) Multi-library per user
- Remove the “single library per user” invariant (RULE-001).
- Allow unlimited libraries per user.
- Repository contract change: `get_by_user_id(user_id) -> Optional[Library]` becomes `list_by_user_id(user_id) -> List[Library]`.
- Database: drop UNIQUE(user_id); add INDEX(user_id) for efficient queries.

2) Flat backend endpoints (filters, not nesting)
- Library: `GET /api/v1/libraries?user_id={id}`, `POST /api/v1/libraries`, `GET /api/v1/libraries/{id}`
- Bookshelf: `GET /api/v1/bookshelves?library_id={id}`, `POST /api/v1/bookshelves` (body includes `library_id`)
- Book: `GET /api/v1/books?bookshelf_id={id}`, `POST /api/v1/books` (body includes `bookshelf_id` and `library_id`)
- Block: `GET /api/v1/blocks?book_id={id}`, `POST /api/v1/blocks` (body includes `book_id`)
- Forbid nested backend routes like `/libraries/{id}/bookshelves` (UI may still use nested URLs for navigation).

3) Page isolation and block editing scope
- Library page shows libraries; Bookshelf page shows bookshelves; Book page shows books; Block appears only within Book editor.
- Keep `/admin/libraries` as a first-class page.
- Optional Library selector in Header is permitted for convenience; it does not replace the Libraries page.
- Explicitly forbid `/admin/blocks/[blockId]` as a standalone page.

## Consequences

- Domain & Repository:
  - Update `ILibraryRepository` to include `list_by_user_id(user_id) -> List[Library]` and migrate implementations.
  - Remove logic relying on UNIQUE(user_id) at database or service layers.

- Database:
  - Migration: drop UNIQUE(libraries.user_id); create INDEX(libraries.user_id).

- API & Adapters:
  - Ensure routers expose only flat endpoints with query filters.
  - POST endpoints that create children must include parent IDs in the body (e.g., `library_id`, `bookshelf_id`, `book_id`).

- Frontend:
  - Update rules and planned endpoints to flat style.
  - Page isolation enforced; Library page remains first-class; Block not standalone.

## Migration Steps

1) Database
- Drop unique constraint on `libraries.user_id`.
- Create an index on `libraries.user_id`.

2) Repository/API
- Replace `get_by_user_id()` usages with `list_by_user_id()`.
- Adjust DTOs and handlers if they assumed a single library per user.

3) Documentation & Rules
- DDD_RULES.yaml: remove RULE-001; revise ORM/constraints to INDEX(user_id); update repository contracts and flows.
- HEXAGONAL_RULES.yaml: mark routing decision as resolved; add library flat routing guidelines; remove references to RULE-001.
- VISUAL_RULES.yaml: update page isolation, library mapping to unlimited, planned endpoints to flat; add rule that Block has no standalone page.

## Status & Verification

- Backend design aligns with Independent Aggregates and flat routes.
- Frontend and backend contracts consistent: query-filtered flat endpoints.
- ADR-071 is now the latest reference in rules metadata.
