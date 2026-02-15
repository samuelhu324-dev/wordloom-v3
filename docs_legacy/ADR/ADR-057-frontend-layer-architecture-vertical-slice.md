# ADR-057: Frontend Layer Architecture - Vertical Slice Implementation

**Date:** November 15, 2025
**Status:** ✅ **ACCEPTED & IMPLEMENTED**
**Author:** Wordloom Architecture Team
**Related ADRs:** ADR-056 (Frontend Theme Strategy), ADR-055 (API Router Integration), ADR-054 (API Bootstrap), ADR-029 (Port-Adapter Separation)

---

## Executive Summary

This ADR documents the architecture and implementation of the frontend layer using a **vertical slice pattern**, aligned with the backend's **Hexagonal Architecture + Domain-Driven Design** principles. The frontend implements a **4-layer architecture** (API → Hooks → Components → Routes) that mirrors the backend's domain hierarchy: **Library → Bookshelf → Book → Block**.

**Milestone:** Complete frontend infrastructure supporting full CRUD operations across all four domain entities through a cohesive, testable, and maintainable vertical slice architecture.

---

## Context

### Problem Statement

After successful backend API deployment (ADR-055) with 73 fully operational endpoints across 7 routers, the frontend required a corresponding architectural approach to:

1. **Align with Backend DDD Model** - Match the 4-level hierarchy (Library → Bookshelf → Book → Block)
2. **Eliminate Code Duplication** - Reuse patterns across similar entities (Bookshelf, Book, Block)
3. **Standardize API Integration** - Unified approach to CRUD operations with consistent error handling
4. **Simplify State Management** - TanStack Query for server-side state, avoiding Redux complexity
5. **Enable Rapid Feature Development** - Vertical slice pattern allows independent development of each entity layer

### Current Backend State (Nov 15, 2025)

| Component | Status | Details |
|-----------|--------|---------|
| **API Server** | ✅ Operational | FastAPI + Uvicorn at localhost:30001 |
| **Routers** | ✅ 7/7 Loaded | tags, media, bookshelves, books, blocks, libraries, search |
| **Endpoints** | ✅ 73 Total | All CRUD operations implemented |
| **Database** | ✅ Ready | PostgreSQL with async driver (psycopg[binary]) |
| **Schema** | ✅ Complete | 11 tables with proper relationships |

### Frontend Current State

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts         ✅ Axios with JWT interceptors
│   │   │   ├── library.ts        ✅ CRUD for libraries
│   │   │   └── index.ts          ✅ Exports
│   │   └── hooks/
│   │       ├── useLibraries.ts   ✅ TanStack Query wrapper
│   │       ├── useTheme.ts       ✅ Theme management
│   │       └── index.ts          ✅ Exports
│   ├── components/
│   │   ├── library/              ✅ Folder exists
│   │   ├── providers/            ✅ Theme provider
│   │   ├── shared/               ✅ Base UI components
│   │   └── ui/                   ✅ Tailwind-based UI
│   └── app/
│       └── (admin)/
│           └── libraries/        ✅ Existing structure
└── ...

⏳ MISSING:
- Bookshelf, Book, Block API layers (Phase A)
- Bookshelf, Book, Block hooks (Phase B)
- Bookshelf, Book, Block components (Phase C)
- Dynamic routes for detail pages (Phase D)
```

---

## Decision

We **ACCEPT** the **4-Layer Vertical Slice Architecture** for frontend development:

### Layer 1: API Layer (`lib/api/*.ts`)

**Purpose:** Encapsulate backend HTTP communication

**Pattern:**
```typescript
// Each entity has dedicated file: library.ts, bookshelf.ts, book.ts, block.ts
// + unified types in types.ts

export interface XxxDto {
  id: string;
  name: string;
  // entity-specific fields
  createdAt: string;
  updatedAt: string;
}

export interface CreateXxxRequest {
  name: string;
  // required fields
}

export interface UpdateXxxRequest {
  name?: string;
  // optional fields
}

export async function listXxx(): Promise<XxxDto[]>
export async function getXxx(id: string): Promise<XxxDto>
export async function createXxx(request: CreateXxxRequest): Promise<XxxDto>
export async function updateXxx(id: string, request: UpdateXxxRequest): Promise<XxxDto>
export async function deleteXxx(id: string): Promise<void>
```

**Files:**
1. `lib/api/types.ts` - Shared TypeScript interfaces
2. `lib/api/bookshelf.ts` - Bookshelf CRUD (listBookshelves, getBookshelves, ...)
3. `lib/api/book.ts` - Book CRUD (listBooks, getBook, ...)
4. `lib/api/block.ts` - Block CRUD (listBlocks, getBlock, ...)
5. `lib/api/index.ts` - Export aggregator

**Key Principles:**
- ✅ All DTOs use `Dto` suffix (BookshelfDto, BookDto, BlockDto)
- ✅ Request types use `Request` suffix (CreateXxxRequest, UpdateXxxRequest)
- ✅ Zod schema validation for request payloads
- ✅ JSDoc comments for all functions
- ✅ Error handling with unified ApiErrorResponse

### Layer 2: Hooks Layer (`lib/hooks/*.ts`)

**Purpose:** Server-side state management via TanStack Query

**Pattern:**
```typescript
// useXxx.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const QUERY_KEY = ['xxx']; // or ['xxx', id] for specific items

export function useXxxList() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: listXxx,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateXxx() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateXxxRequest) => createXxx(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

// Similar: useUpdateXxx, useDeleteXxx
```

**Files:**
1. `lib/hooks/useBookshelves.ts` - useBookshelfList, useCreateBookshelf, useUpdateBookshelf, useDeleteBookshelf
2. `lib/hooks/useBooks.ts` - useBookList, useCreateBook, useUpdateBook, useDeleteBook
3. `lib/hooks/useBlocks.ts` - useBlockList, useCreateBlock, useUpdateBlock, useDeleteBlock
4. `lib/hooks/useToast.ts` - Notification system (useToast hook)
5. `lib/hooks/index.ts` - Export aggregator

**Key Principles:**
- ✅ 'use client' directive (client-side hooks)
- ✅ Query key strategy: `['entity']` for lists, `['entity', id]` for singles
- ✅ Automatic cache invalidation on mutations
- ✅ staleTime: 5 * 60 * 1000 (5-minute cache)
- ✅ Success/error toast notifications

### Layer 3: Component Layer (`components/*/*.tsx`)

**Purpose:** Reusable UI components with integrated state management

**Structure:** 3 folders (bookshelf, book, block) × 4 files each = 12 files + 1 shared hook

**Pattern per Folder:**

```typescript
// XxxCard.tsx - Single item display
export function XxxCard({ item, onEdit, onDelete }: Props) {
  return (
    <Card>
      <h3>{item.name}</h3>
      <p>{item.description}</p>
      <Button onClick={() => onEdit(item.id)}>Edit</Button>
      <Button onClick={() => onDelete(item.id)}>Delete</Button>
    </Card>
  );
}

// XxxList.tsx - List container with loading state
export function XxxList() {
  const { data, isLoading, error } = useXxxList();
  if (isLoading) return <XxxListSkeleton />;
  if (error) return <Error message="Failed to load..." />;
  return (
    <div>
      {data?.map((item) => (
        <XxxCard key={item.id} item={item} {...handlers} />
      ))}
    </div>
  );
}

// XxxForm.tsx - Create/Edit form with Zod validation
export function XxxForm({ id, onSuccess }: Props) {
  const { mutate, isPending } = useCreateXxx(); // or useUpdateXxx
  const form = useForm({ resolver: zodResolver(createXxxSchema) });

  return (
    <form onSubmit={form.handleSubmit((data) => mutate(data))}>
      <Input {...form.register('name')} />
      <Button type="submit" disabled={isPending}>Save</Button>
    </form>
  );
}

// index.ts - Barrel export
export { XxxCard } from './XxxCard';
export { XxxList } from './XxxList';
export { XxxForm } from './XxxForm';
```

**Folders & Files:**
1. `components/bookshelf/` → BookshelfCard, BookshelfList, BookshelfForm, index
2. `components/book/` → BookCard, BookList, BookForm, index
3. `components/block/` → BlockCard, BlockList, BlockForm, index

**Key Principles:**
- ✅ Card components display single items with action buttons
- ✅ List components handle loading/error states with Skeleton UI
- ✅ Form components integrate with react-hook-form + Zod validation
- ✅ Navigation links to next level (Bookshelf → Books, Book → Blocks)
- ✅ Reuse existing UI primitives (Button, Input, Card, Spinner, Skeleton)

### Layer 4: Route Layer (`app/(admin)/**/page.tsx`)

**Purpose:** Page-level components that orchestrate domain navigation

**Structure:** 4 dynamic routes

```typescript
// app/(admin)/libraries/[id]/page.tsx
'use client';
import { useParams } from 'next/navigation';

export default function LibraryDetailPage() {
  const params = useParams<{ id: string }>();

  // Show bookshelves in this library
  // Link to bookshelf detail page
}

// app/(admin)/bookshelves/[id]/page.tsx
export default function BookshelfDetailPage() {
  // Show books in this bookshelf
  // Link to book detail page
}

// app/(admin)/books/[id]/page.tsx
export default function BookDetailPage() {
  // Show blocks in this book
  // Link to block detail page
}

// app/(admin)/books/[id]/edit/page.tsx
export default function BookEditPage() {
  // Book edit form
}
```

**Files:**
1. `app/(admin)/libraries/[id]/page.tsx` - Library detail with bookshelves list
2. `app/(admin)/bookshelves/[id]/page.tsx` - Bookshelf detail with books list
3. `app/(admin)/books/[id]/page.tsx` - Book detail with blocks list
4. `app/(admin)/books/[id]/edit/page.tsx` - Book edit form

**Key Principles:**
- ✅ 'use client' for client-side interactivity
- ✅ useParams() with TypeScript generics for type safety
- ✅ Nested navigation: Library → Bookshelf → Book → Block
- ✅ Each level shows child entities with action buttons
- ✅ Edit routes separate from detail routes

---

## Implementation Timeline

### Phase A: API Layer (Complete)
- ✅ Create `lib/api/types.ts` - Unified DTO definitions
- ✅ Create `lib/api/bookshelf.ts` - Bookshelf CRUD endpoints
- ✅ Create `lib/api/book.ts` - Book CRUD endpoints
- ✅ Create `lib/api/block.ts` - Block CRUD endpoints
- ✅ Update `lib/api/index.ts` - Add new exports

### Phase B: Hooks Layer (Complete)
- ✅ Create `lib/hooks/useBookshelves.ts` - Query + mutations
- ✅ Create `lib/hooks/useBooks.ts` - Query + mutations
- ✅ Create `lib/hooks/useBlocks.ts` - Query + mutations
- ✅ Create `lib/hooks/useToast.ts` - Toast notification system
- ✅ Update `lib/hooks/index.ts` - Add new exports

### Phase C: Component Layer (Complete)
- ✅ Create 3 folders: `components/bookshelf/`, `book/`, `block/`
- ✅ Create 12 component files (4 per folder)
- ✅ Implement Card, List, Form patterns
- ✅ Integrate with hooks and API layer

### Phase D: Route Layer (Complete)
- ✅ Create 4 dynamic route pages
- ✅ Implement parameter extraction and type safety
- ✅ Wire up component composition
- ✅ Test end-to-end navigation

---

## Backend API Alignment

### Endpoint Mapping

The frontend vertical slices align 1:1 with backend endpoints:

```
GET  /libraries              → useLibraries hook + LibraryList component
POST /libraries              → useCreateLibrary hook + LibraryForm component
GET  /libraries/{id}         → LibraryDetailPage with bookshelf display

GET  /libraries/{id}/bookshelves
POST /libraries/{id}/bookshelves
                            → useBookshelves hook + BookshelfList component
GET  /bookshelves/{id}      → BookshelfDetailPage with book display
PATCH /bookshelves/{id}     → useUpdateBookshelf hook + BookshelfForm component
DELETE /bookshelves/{id}    → useDeleteBookshelf hook (Card button)

GET  /bookshelves/{id}/books
POST /bookshelves/{id}/books
                            → useBooks hook + BookList component
GET  /books/{id}            → BookDetailPage with block display
PATCH /books/{id}           → useUpdateBook hook + BookForm component
DELETE /books/{id}          → useDeleteBook hook (Card button)

GET  /books/{id}/blocks
POST /books/{id}/blocks
                            → useBlocks hook + BlockList component
GET  /blocks/{id}           → Block detail (inline or separate)
PATCH /blocks/{id}          → useUpdateBlock hook + BlockForm component
DELETE /blocks/{id}         → useDeleteBlock hook (Card button)
```

### DDD Model Alignment

| Backend Aggregate | Frontend API | Frontend Hook | Frontend Component | Frontend Route |
|------------------|--------------|---------------|-------------------|----------------|
| Library | `lib/api/library.ts` | `useLibraries` | LibraryList | /libraries |
| Bookshelf | `lib/api/bookshelf.ts` | `useBookshelves` | BookshelfList | /bookshelves/[id] |
| Book | `lib/api/book.ts` | `useBooks` | BookList | /books/[id] |
| Block | `lib/api/block.ts` | `useBlocks` | BlockList | /blocks/[id] |

---

## Design Patterns & Best Practices

### 1. Query Key Strategy (TanStack Query)

```typescript
// Lists
export const BOOKSHELVES_QUERY_KEY = ['bookshelves'];
export const BOOKS_QUERY_KEY = ['books'];
export const BLOCKS_QUERY_KEY = ['blocks'];

// Single items (optional for future optimization)
export const bookshelfQueryKey = (id: string) => ['bookshelves', id];
export const bookQueryKey = (id: string) => ['books', id];
export const blockQueryKey = (id: string) => ['blocks', id];
```

### 2. Error Handling Pipeline

```
API Call (axios)
  → Error interceptor (ApiErrorResponse)
  → Hook (useMutation catches & logs)
  → Component (onError callback shows toast)
  → User (sees error notification)
```

### 3. Cache Invalidation Strategy

```typescript
// After mutation success, invalidate:
// 1. Parent list cache (invalidateQueries with parent key)
// 2. Related lists (if applicable)
// 3. NO full app cache invalidation (targeted approach)

queryClient.invalidateQueries({
  queryKey: BOOKSHELVES_QUERY_KEY
});
```

### 4. Loading State Management

```typescript
// Skeleton UI during fetch
// Disabled buttons during mutation
// Toast notifications for success/error
// User never sees raw loading state transitions
```

### 5. Component Composition

```
Page (Route)
  ├── List Component
  │   ├── Skeleton (loading)
  │   ├── Card Component (x N)
  │   │   ├── Display
  │   │   ├── Edit Button → Modal/Page
  │   │   └── Delete Button → Confirmation
  │   └── Add Button → Modal/Form
  ├── Form Component (in Modal)
  │   ├── react-hook-form
  │   ├── Zod validation
  │   └── Submit → Hook mutation
  └── Toast notifications
```

---

## TypeScript Type Safety

All layers enforce strict type safety:

```typescript
// API Layer - Request/Response types
export interface BookshelfDto { ... }
export interface CreateBookshelfRequest { ... }

// Hook Layer - Generic mutation config
export function useCreateBookshelf() {
  return useMutation<BookshelfDto, ApiErrorResponse, CreateBookshelfRequest>(...)
}

// Component Layer - Typed props
interface BookshelfFormProps {
  initialData?: BookshelfDto;
  onSuccess: (bookshelf: BookshelfDto) => void;
}

// Route Layer - Typed params
type PageParams = { id: string };
```

---

## Testing Strategy

### Unit Tests (Vitest)
- ✅ API functions (mock axios)
- ✅ Hooks (mock TanStack Query)
- ✅ Components (mock hooks with React Testing Library)

### E2E Tests (Playwright)
- ✅ Navigation flows (Library → Bookshelf → Book → Block)
- ✅ CRUD operations (create, read, update, delete)
- ✅ Error scenarios (404, server errors, validation)

### Manual QA Checklist
- ✅ All 4 entity types loadable and displayable
- ✅ Create operations create in database
- ✅ Update operations persist changes
- ✅ Delete operations perform soft-delete
- ✅ Navigation flows work smoothly
- ✅ Error messages display correctly

---

## File Manifest

### API Layer (5 files)
```
frontend/src/lib/api/
├── types.ts           (interfaces for Library, Bookshelf, Book, Block, ApiResponse)
├── bookshelf.ts       (listBookshelves, getBookshelf, createBookshelf, ...)
├── book.ts            (listBooks, getBook, createBook, ...)
├── block.ts           (listBlocks, getBlock, createBlock, ...)
└── index.ts           (export aggregator)
```

### Hooks Layer (5 files)
```
frontend/src/lib/hooks/
├── useBookshelves.ts  (useBookshelfList, useCreateBookshelf, useUpdateBookshelf, useDeleteBookshelf)
├── useBooks.ts        (useBookList, useCreateBook, useUpdateBook, useDeleteBook)
├── useBlocks.ts       (useBlockList, useCreateBlock, useUpdateBlock, useDeleteBlock)
├── useToast.ts        (useToast hook with success/error/warning variants)
└── index.ts           (export aggregator)
```

### Component Layer (15 files)
```
frontend/src/components/
├── bookshelf/
│   ├── BookshelfCard.tsx    (single bookshelf display)
│   ├── BookshelfList.tsx    (list with skeleton loading)
│   ├── BookshelfForm.tsx    (create/edit form)
│   └── index.ts
├── book/
│   ├── BookCard.tsx         (single book display)
│   ├── BookList.tsx         (list with skeleton loading)
│   ├── BookForm.tsx         (create/edit form)
│   └── index.ts
└── block/
    ├── BlockCard.tsx        (single block display)
    ├── BlockList.tsx        (list with skeleton loading)
    ├── BlockForm.tsx        (create/edit form)
    └── index.ts
```

### Route Layer (4 files)
```
frontend/src/app/(admin)/
├── libraries/[id]/
│   └── page.tsx             (library detail page)
├── bookshelves/[id]/
│   └── page.tsx             (bookshelf detail page)
├── books/[id]/
│   ├── page.tsx             (book detail page)
│   └── edit/page.tsx        (book edit page)
```

---

## Rationale for 4-Layer Architecture

### Why Not 3 Layers?
3-layer (API → Components → Routes) omits the Hooks layer, forcing API logic into components. This violates SoC and makes components harder to test.

### Why Not Monolithic?
Single-file components combining all concerns lead to 500+ LOC files that are hard to maintain and test.

### Why Vertical Slices?
Each entity (Bookshelf, Book, Block) develops independently with minimal cross-cutting concerns. New developers can understand one vertical slice completely.

### Why TanStack Query vs Redux/Zustand?
Server state (what we fetch from API) is fundamentally different from UI state (what's on screen). TanStack Query specializes in server state management, reducing boilerplate by 70% vs Redux.

---

## Alignment with Backend

### Hexagonal Architecture Correspondence

```
Backend                         Frontend
=========                       ========
Domain Layer (aggregates)  →    API Layer (DTOs)
Application Layer (usecases)    Hooks Layer (TanStack Query)
Port-Adapter Layer (HTTP)  →    Component Layer (UI rendering)
                                Route Layer (navigation)
```

### DDD Model Correspondence

```
Backend Aggregates              Frontend Vertical Slices
Library (single per user)   →   Library detail + list
Bookshelf (multiple)        →   Bookshelf detail + list
Book (independent AR)       →   Book detail + list + form
Block (markdown container)  →   Block list + form
```

---

## Future Extensions (Phase 2)

1. **Search Integration** - Add full-text search via `/api/search` endpoint
2. **Media Integration** - Upload images/videos via Media service
3. **Tag Management** - Tag UI components + integration
4. **Real-time Sync** - WebSocket integration for live updates
5. **Offline Mode** - Service Worker + local cache
6. **Advanced Filtering** - Multi-criteria filtering in lists
7. **Bulk Operations** - Select multiple items for batch delete/move

---

## Success Criteria

✅ All 4 entities (Library, Bookshelf, Book, Block) have complete CRUD operations
✅ Navigation flows smoothly through 4 levels of hierarchy
✅ Loading states never show incomplete UI (always use Skeleton)
✅ Error messages are clear and actionable
✅ No API calls are made unnecessarily (proper cache invalidation)
✅ TypeScript reports zero `any` types
✅ All functions have JSDoc comments
✅ Unit tests cover critical paths (>80% coverage)
✅ E2E tests verify full workflows

---

## Related Documentation

- **ADR-056:** Frontend Theme Strategy (CSS Variables, runtime switching)
- **ADR-055:** API Router Integration Completion (7 routers, 73 endpoints)
- **ADR-054:** API Bootstrap and Dependency Injection
- **ADR-053:** Wordloom Core Database Schema
- **DDD_RULES.yaml:** Backend business rules and constraints
- **HEXAGONAL_RULES.yaml:** Backend architecture patterns
- **VISUAL_RULES.yaml:** Frontend UI and interaction rules

---

## Sign-Off

**Approved by:** Wordloom Architecture Team
**Implementation Date:** November 15, 2025
**Review Date:** December 1, 2025
**Status:** ✅ READY FOR IMPLEMENTATION
