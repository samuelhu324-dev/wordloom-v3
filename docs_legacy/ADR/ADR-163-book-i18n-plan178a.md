# ADR-163: Book Widget Bilingual Refresh (Plan178A)

## Status
Accepted – December 7, 2025

## Context
- Even after the bookshelf dashboard i18n pass (Plan177A), the BookMainWidget stack inside `/admin/bookshelves/[id]` still mixed zh-CN copy with English controls, especially inside maturity sections, filter/search bars, and action menus.
- Card components (BookFlatCard, BookRowCard, BookShowcaseItem) duplicated toast/tooltip strings and hard-coded aria labels, making accessibility text diverge from what the user saw on screen.
- Helper utilities such as `bookVisuals.ts` emitted relative times and block counts in Chinese regardless of the language switcher, so combined views produced hybrid sentences and broke UX tests.

## Decision
1. Add a dedicated `books.*` namespace to `en-US.ts` and `zh-CN.ts`, covering headers, filter/search controls, maturity section titles, empty states, toast/confirm copy, aria labels, and tooltip text.
2. Wire `useI18n()` through `BookMainWidget`, `BookMainWidgetHeader`, `BookMaturityFilterBar`, `BookMaturitySearchBar`, `BookMaturityView`, and `BookshelfBooksSection`, replacing every literal string (including `aria-*`, quick actions, and error fallbacks) with `t()` lookups.
3. Update `BookFlatCard`, `BookRowCard`, and `BookShowcaseItem` plus supporting menus to read from the new namespace and route destructive / basement move toasts through translations.
4. Localize helper logic by passing the active `lang` into `bookVisuals.ts` (relative time + block count formatters) and consolidating dynamic interpolations (keywords, counters, book titles) via `t(key, params)` so combined mode, search summaries, and empty/error states always match the selected locale.

## Consequences
- The entire Book widget experience mirrors bookshelf/library behavior: toggling the language switch immediately updates headers, controls, tooltips, aria labels, and toast messages without mixed-language artifacts.
- Accessibility improves because assistive technology now receives localized descriptions that match what sighted users read, and destructive confirmations can be audited via the dictionary instead of scattered literals.
- Shared helpers reduce regressions: future additions to Book widgets can extend `books.*` keys instead of sprinkling strings across components, and locale-aware relative time keeps QA screenshots consistent.
- QA scope narrows to verifying translations rather than hunting for missing literals, enabling the localization team to review copy centrally within the dictionaries.
