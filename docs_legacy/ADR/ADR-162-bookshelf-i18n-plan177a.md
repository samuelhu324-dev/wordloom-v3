# ADR-162: Bookshelf Dashboard Bilingual Refresh (Plan177A)

## Status
Accepted – December 7, 2025

## Context
- After the library list (Plan176A) adopted the i18n layer, the Bookshelf Dashboard (/admin/libraries/[libraryId] and /admin/bookshelves) still mixed zh-CN strings with English tooltips and toasts.
- Key workflows (sorting/filtering, search, pinned sections, destructive actions) exposed untranslated copy and inconsistent aria labels, breaking the visual rules checklist.
- Dashboards also rendered relative timestamps without respecting the active locale, so switching the language switcher produced hybrid output.

## Decision
1. Extend the locale dictionaries with a dedicated `bookshelves.*` keyset that covers stats cards, search placeholders, table headers, empty states, badges, action tooltips, and toast/confirm copy.
2. Update `BookshelfDashboardBoard`, `BookshelfDashboardCard`, `BookshelfHeader`, and the Library detail hero + creation dialog to consume `useI18n()`, wiring every fixed string (including aria labels) through `t()`.
3. Normalize temporal formatting by passing the current `lang` into the relative time helper, and ensure all toast/confirm flows (pin/unpin, archive/restore, delete, creation quota) reuse the shared translations.

## Consequences
- Bookshelf UI now mirrors the library page: flipping the language switch immediately re-renders headings, controls, tooltips, and dialogs without mixed copy.
- Accessibility improves because aria labels/descriptions stay in sync with visible text, and destructive confirmations always surface bilingual guidance.
- The new `bookshelves.*` namespace creates a reusable contract for future modules (Basement, Book widgets) that reference bookshelf metrics or actions.
