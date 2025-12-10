Plan For Bookshelf Page i18n Toggle (Plan177A)
Status: ✅ Completed (2025-12-07)

## Implementation Notes

- Added `bookshelves.*` namespace entries covering dashboard stats, search hints, table headers, pinned labels, tag chips, maturity tooltips, metrics tooltips, action buttons, empty/error states, and toast/confirm strings in both locales.
- Refactored `BookshelfDashboardBoard` to pull every label (sort/filter controls, search, section titles, table columns, loading/error/empty copy) from `useI18n()`, including aria text.
- Updated `BookshelfDashboardCard` to use locale-aware relative time formatting and translated badges/tooltips/tag placeholders/action buttons, ensuring all aria-labels and data-tooltips are bilingual.
- Wired `LibraryDetailPage` hero, snapshot summary, limit notice, breadcrumb buttons, and shared `LibraryForm` create dialog to reuse `bookshelves.*` keys so the inline Create Bookcase modal matches the dashboard.
- Localized `BookshelfHeader` cover alt/title button to keep hero visuals accessible in both languages.
- Verified the language switcher forces rerender without stale copy (manual QA on `npm run dev` with zh-CN ↔ en-US toggles), and no missing-key warnings remained.

Identify the bookshelf page components in frontend/src/** that render the stats cards, filters, table headers, buttons, and empty states; list all hard-coded text.
Confirm existing i18n setup (e.g., next-i18next, locale JSONs under frontend/public/locales/** or similar) to understand naming, namespaces, and hooks already in use.
For each UI string on the bookshelf page, create translation keys (group them by namespace like bookshelf for clarity) and add both English and Chinese entries in the locale files.
Update the bookshelf page components to pull strings via the translation hook/helper, ensuring dynamic values (counts, status labels) are interpolated.
Verify the language switcher already present triggers rerenders; if not, ensure the bookshelf page subscribes properly (e.g., useTranslation hook) so toggling languages reflects immediately.
Run the relevant frontend tests or a quick manual check (npm run dev + switch languages) to confirm both locales show correct text and no missing key warnings.
Once you’re ready, let me know and I’ll execute this plan step-by-step.

## Linked Documents
- VISUAL_RULES.yaml → `library_i18n_refresh` / `bookshelf_i18n_refresh` sections
- ADR-161 – Library Page Bilingual Refresh (Plan176A)
- ADR-162 – Bookshelf Dashboard Bilingual Refresh (Plan177A follow-up)