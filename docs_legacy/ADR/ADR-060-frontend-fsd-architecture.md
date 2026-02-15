# ADR-060: Frontend FSD Architecture Implementation

**Date**: 2025-11-16
**Status**: Implemented
**Context**: Complete frontend rebuild using Feature-Sliced Design (FSD) pattern
**Decision**: Implement strict 6-layer FSD architecture with unified domain model

## Problem Statement

Previous frontend had:
- 45 scattered components across 10 folders → No clear module boundaries
- Tag/Media/Search only had UI components → Missing hooks/API layers
- 404 errors and encoding issues → Not worth fixing
- Ad-hoc folder structure → Hard to maintain and extend

## Solution: Feature-Sliced Design (FSD)

Adopted strict FSD architecture with 6 layers:

```
src/
├── shared/          # Layer 0: Infrastructure
│   ├── api/         # HTTP client (Axios + JWT interceptor)
│   ├── lib/         # Utilities, config
│   ├── ui/          # Base components (Button, Card, Input, Spinner, Modal)
│   ├── styles/      # Design tokens (CSS Variables)
│   └── providers/   # Global providers (QueryProvider, ThemeProvider)
│
├── entities/        # Layer 1: Domain models (7 aggregates)
│   ├── library/     # LibraryDto types
│   ├── bookshelf/   # BookshelfDto types
│   ├── book/        # BookDto types
│   ├── block/       # BlockDto types (fractional_index)
│   ├── tag/         # TagDto types
│   ├── media/       # MediaDto types (trash lifecycle)
│   └── search/      # SearchResultDto types
│
├── features/        # Layer 2: Feature business logic (7 features)
│   ├── library/     # Library CRUD + UI
│   ├── bookshelf/   # Bookshelf CRUD + UI
│   ├── book/        # Book CRUD + UI
│   ├── block/       # Block CRUD + UI
│   ├── tag/         # Tag CRUD + UI
│   ├── media/       # Media list + restore
│   └── search/      # Search + results display
│
├── widgets/         # Layer 3: Composed features (coming)
│   ├── library/
│   ├── bookshelf/
│   ├── book/
│   └── block/
│
├── layouts/         # Layer 4: Page layouts (coming)
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── Layout.tsx
│
├── pages/           # Layer 5: Next.js pages (App Router)
│   ├── (admin)/
│   │   ├── libraries/
│   │   ├── bookshelves/
│   │   ├── books/
│   │   ├── blocks/
│   │   ├── tags/
│   │   ├── media/
│   │   ├── search/
│   │   └── dashboard/
│   ├── (auth)/
│   │   └── login/
│   └── page.tsx     # Home
│
└── app/             # Layer 6: Root layout & providers
    ├── layout.tsx
    ├── providers.tsx
    └── page.tsx
```

## Architecture Decisions

### 1. Unified Domain Model (7 Aggregates)

**Problem**: Previous code had Tag/Media/Search UI without proper API/hooks layers.

**Solution**: Each domain has consistent 3-layer structure:
- **model/api.ts**: HTTP operations (list/get/create/update/delete)
- **model/hooks.ts**: TanStack Query hooks with query key strategy
- **ui/**: React components with TypeScript interfaces

**Example - Library Feature**:
```typescript
// features/library/model/api.ts
export const listLibraries = async (): Promise<LibraryDto[]> => { ... }

// features/library/model/hooks.ts
export const useLibraries = () => useQuery({
  queryKey: QUERY_KEY.all,
  queryFn: listLibraries
})

// features/library/ui/LibraryCard.tsx
export const LibraryCard = ({ library, onSelect }) => { ... }
```

### 2. Query Key Strategy

Prevents cache invalidation bugs:
```typescript
const QUERY_KEY = {
  all: ['libraries'],
  detail: (id) => [...QUERY_KEY.all, id]
}

// Auto-invalidates when needed
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: QUERY_KEY.all })
}
```

### 3. CSS Variable Design System

Enables theme switching without component rewrites:
```css
/* tokens.css */
--color-primary: #2563eb;
--color-secondary: #64748b;
--spacing-md: 0.75rem;
--radius-md: 0.375rem;
```

Used in all components:
```typescript
<div style={{ color: 'var(--color-primary)' }}>
```

### 4. Public API Exports

Each layer has `index.ts` for clean imports:
```typescript
// features/library/index.ts
export * from './model/api'
export * from './model/hooks'
export * from './ui'

// Usage
import { useLibraries, LibraryCard } from '@/features/library'
```

### 5. Strict Layer Dependencies

**Allowed**: Layer N can import from layers 0 to N-1
**Forbidden**: Backward imports (features can't import from pages)

This prevents circular dependencies and maintains clean architecture.

## Implementation Details

### Shared Layer (0)

**API Client** (`shared/api/client.ts`):
- Axios configured with JWT interceptor
- Automatic token refresh handling
- Global error handling

**UI Components** (`shared/ui/`):
- Button, Card, Input, Spinner, Modal
- Consistent TypeScript interfaces
- CSS Module styling

**Utilities** (`shared/lib/utils.ts`):
- formatDate, debounce, formatFileSize, etc.

### Entities Layer (1)

7 TypeScript interfaces for each domain:
- LibraryDto, BookshelfDto, BookDto, BlockDto
- TagDto, MediaDto, SearchResultDto
- Includes validation constraints and optional fields

### Features Layer (2)

Each feature has 2 files + components:

**model/api.ts**: HTTP operations
- list, get, create, update, delete
- Handles complex paths (nested resources)
- Returns typed DTOs

**model/hooks.ts**: TanStack Query hooks
- useX (queries), useCreateX (mutations)
- Cache invalidation on mutations
- Query key strategy for consistency

**ui/**: React components
- Functional components with React.forwardRef
- TypeScript props interfaces
- CSS Modules for styling
- Reusable and composable

### Pages Layer (5)

Next.js App Router structure:
```
app/
├── page.tsx               # Home page
├── layout.tsx             # Root layout with providers
├── (admin)/
│   ├── layout.tsx         # Admin layout
│   ├── libraries/page.tsx # Libraries list
│   ├── bookshelves/page.tsx
│   ├── books/page.tsx
│   ├── tags/page.tsx
│   ├── media/page.tsx
│   ├── search/page.tsx
│   └── dashboard/page.tsx
└── (auth)/
    └── login/page.tsx
```

## Benefits

1. **Clear Module Boundaries**: Each feature self-contained with public API
2. **Testability**: Separate model/ui layers easy to unit test
3. **Reusability**: Shared components used across features
4. **Maintainability**: One change won't break unrelated features
5. **Scalability**: New features follow same pattern
6. **Type Safety**: Full TypeScript everywhere

## File Structure Summary

**Total files created**: 80+

### Breakdown:
- **Shared layer**: 15 files (API, UI, styles, utilities)
- **Entities layer**: 7 files (type definitions)
- **Features layer**: 42 files (7 features × 6 files)
- **Pages layer**: 10 files (routes)
- **Config files**: 5 files (tsconfig, package.json, next.config, etc.)

### By category:
- **TypeScript**: 45 files (.ts, .tsx)
- **CSS Modules**: 25 files (.module.css)
- **Config**: 5 files (.json, .js)
- **Markdown**: 0 (documentation in ADR)

## Next Steps (Coming Soon)

1. **npm install** - Install dependencies (React, Next.js, Axios, TanStack Query)
2. **Widgets layer** - Compose features into layout widgets
3. **Layout components** - Header, Sidebar, Navigation
4. **Theme provider** - CSS variable injection + switching
5. **Integration tests** - Test unified Library→Bookshelf→Book→Block navigation

## Related ADRs

- ADR-057: Frontend Layer Architecture (Previous design, superseded)
- ADR-056: Theme Strategy (CSS Variables approach)
- ADR-055: API Router Integration

## References

- [Feature-Sliced Design](https://feature-sliced.design/) - Official FSD documentation
- [Tinkoff FSD Standard](https://www.notion.so/FSD-c6fde7e4ba1d48578e0e5bb7e6b7c0f0)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Next.js App Router](https://nextjs.org/docs/app)

---

**Decision Record**: Frontend uses FSD architecture with unified domain model, strict 6-layer structure, and public API exports. All 7 domains (Library/Bookshelf/Book/Block/Tag/Media/Search) have consistent model and UI layers. CSS Variables enable theme switching. TanStack Query with query key strategy prevents cache bugs.
