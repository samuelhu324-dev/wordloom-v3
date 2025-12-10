# ADR-161: Library Page Bilingual Refresh (Plan176A)

## Status
Accepted – December 7, 2025

## Context
- The admin library page (/admin/libraries) still contained a mix of hard-coded Chinese copy and ad-hoc English phrases.
- Earlier plans (Plan175/Plan177) aligned tooltips and cover visuals, but i18n coverage remained incomplete, leading to accessibility issues and confusing UX when switching locales.
- Recent visual rules require every tooltip, aria label, and toast to provide bilingual content.

## Decision
1. Extend `src/i18n/locales/en-US.ts` and `zh-CN.ts` with the full `libraries.*` keyset (list sections, card actions, dialogs, form labels, tag helpers, tooltips, toasts).
2. Update all library-facing components to consume `useI18n`:
   - `LibraryMainWidget`, `LibraryList`
   - `LibraryCard`, `LibraryCardHorizontal`
   - `LibraryForm`, `LibraryTagsRow`
3. Introduce locale-aware helpers (`formatRelative`, `formatAbsoluteDateTime`, `formatDate`) and pass the current `lang` when rendering card/list timestamps.
4. Ensure Tag-related components reuse the shared translations, and fix runtime order issues (`tagEmptyHint` defined before use).

## Consequences
- Library UI now switches cleanly between zh-CN and en-US without mixed copy.
- Tooltips/aria labels meet the accessibility requirement documented in VISUAL_RULES.
- Tag selector status/error messages stay consistent with the rest of the UI, preventing runtime ReferenceErrors.
- Future surfaces (Tags/Basement) can reuse the same `libraries.*` dictionary entries for consistent terminology.
