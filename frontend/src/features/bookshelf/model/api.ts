import { apiClient } from '@/shared/api';
import {
  BookshelfDto,
  CreateBookshelfRequest,
  UpdateBookshelfRequest,
  toBookshelfDto,
  BackendBookshelf,
  BookshelfDashboardItemDto,
  BackendBookshelfDashboardItem,
  BackendBookshelfDashboardSnapshot,
  BookshelfDashboardSnapshot,
  BookshelfDashboardHealthBuckets,
  BookshelfDashboardSort,
  BookshelfDashboardFilter,
  toBookshelfDashboardItem,
} from '@/entities/bookshelf';

// Pagination + cache helpers
const DEFAULT_PAGE_SIZE = 100;
export const BOOKSHELF_LIST_DEFAULT_PAGE_SIZE = DEFAULT_PAGE_SIZE;
const cacheKeySuffix = (libraryId?: string, page?: number, pageSize?: number) =>
  `${libraryId || 'all'}_${page || 1}_${pageSize || DEFAULT_PAGE_SIZE}`;
const bookshelvesCacheKey = (libraryId?: string, page?: number, pageSize?: number) =>
  `wl_bookshelves_cache_${cacheKeySuffix(libraryId, page, pageSize)}`;
const bookshelvesDurationKey = (libraryId?: string, page?: number, pageSize?: number) =>
  `wl_bookshelves_last_duration_ms_${cacheKeySuffix(libraryId, page, pageSize)}`;

interface BackendBookshelfPaginatedResponseV2 {
  items: BackendBookshelf[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface BackendBookshelfPaginatedResponseV1 {
  items: BackendBookshelf[];
  total: number;
}

type BackendBookshelfPaginatedResponse =
  | BackendBookshelfPaginatedResponseV2
  | BackendBookshelfPaginatedResponseV1;

export interface BookshelfListPage {
  items: BookshelfDto[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ListBookshelvesOptions {
  libraryId?: string;
  page?: number;
  pageSize?: number;
}

interface BackendBookshelfDashboardResponse {
  items: BackendBookshelfDashboardItem[];
  total: number;
  page: number;
  page_size: number;
  snapshot?: BackendBookshelfDashboardSnapshot | null;
}

export interface BookshelfDashboardPage {
  items: BookshelfDashboardItemDto[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  snapshot: BookshelfDashboardSnapshot;
}

export interface FetchBookshelfDashboardOptions {
  libraryId: string;
  page?: number;
  size?: number;
  sort?: BookshelfDashboardSort;
  statusFilter?: BookshelfDashboardFilter;
  fallbackThemeColor?: string;
}

/** Validate UUID format */
const isValidUUID = (uuid: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};

/** List bookshelves with Pagination V2 response */
export const listBookshelves = async (options: ListBookshelvesOptions = {}): Promise<BookshelfListPage> => {
  const { libraryId, page = 1, pageSize = DEFAULT_PAGE_SIZE } = options;
  const start = performance.now();

  // Validate libraryId if provided
  if (libraryId && !isValidUUID(libraryId)) {
    console.error(`[listBookshelves] Invalid UUID format: ${libraryId}`);
    throw new Error(`Invalid library_id format: ${libraryId}`);
  }

  const params: string[] = [];
  if (libraryId) params.push(`library_id=${libraryId}`);
  const skip = Math.max(0, (page - 1) * pageSize);
  params.push(`skip=${skip}`);
  params.push(`limit=${pageSize}`);
  const query = params.length ? `?${params.join('&')}` : '';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
    console.log(`[listBookshelves] Fetching from /bookshelves${query}`);
    const response = await apiClient.get<BackendBookshelfPaginatedResponse>(`/bookshelves${query}`,
      { signal: controller.signal }
    );
    const payload = response.data ?? ({} as BackendBookshelfPaginatedResponse);
    const rawItems = Array.isArray((payload as any)?.items) ? (payload as any).items : [];
    const total = typeof (payload as any)?.total === 'number' ? (payload as any).total : rawItems.length;
    let hasMore: boolean;
    if (typeof (payload as any)?.has_more === 'boolean') {
      hasMore = (payload as any).has_more;
    } else {
      hasMore = skip + rawItems.length < total;
      console.warn('[listBookshelves] Missing has_more, derived fallback will be removed after 2025-12-15.'); // TODO:REMOVE-V1-COMPAT
    }
    const normalized: BookshelfListPage = {
      items: rawItems.map(toBookshelfDto),
      total,
      page: typeof (payload as any)?.page === 'number' ? (payload as any).page : page,
      page_size: typeof (payload as any)?.page_size === 'number' ? (payload as any).page_size : pageSize,
      has_more: hasMore,
    };

    // Cache successful response
    try {
      localStorage.setItem(
        bookshelvesCacheKey(libraryId, page, pageSize),
        JSON.stringify({
          items: rawItems,
          total: normalized.total,
          page: normalized.page,
          page_size: normalized.page_size,
          has_more: normalized.has_more,
        })
      );
      localStorage.setItem(
        bookshelvesDurationKey(libraryId, page, pageSize),
        String(Math.round(performance.now() - start))
      );
    } catch {}

    console.log(`[listBookshelves] Success: ${normalized.items.length} items, ${(performance.now() - start).toFixed(0)}ms`);
    return normalized;
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      // Timeout fallback from cache
      console.warn(`[listBookshelves] Timeout after 3s, attempting cache fallback`);
      try {
        const cached = localStorage.getItem(bookshelvesCacheKey(libraryId, page, pageSize));
        if (cached) {
          const parsed = JSON.parse(cached);
          const cachedItems = Array.isArray(parsed?.items) ? parsed.items : [];
          console.log(`[listBookshelves] Returned ${cachedItems.length} items from cache`);
          return {
            items: cachedItems.map(toBookshelfDto),
            total: typeof parsed?.total === 'number' ? parsed.total : cachedItems.length,
            page: typeof parsed?.page === 'number' ? parsed.page : page,
            page_size: typeof parsed?.page_size === 'number' ? parsed.page_size : pageSize,
            has_more: typeof parsed?.has_more === 'boolean' ? parsed.has_more : false,
          };
        }
      } catch {}
      console.warn('Bookshelves request timeout (3s) with no cache fallback');
    }
    console.error(`[listBookshelves] Error:`, err);
    throw err;
  } finally {
    clearTimeout(timeout);
  }
};

/** Get single bookshelf by ID */
export const getBookshelf = async (bookshelfId: string): Promise<BookshelfDto> => {
  const response = await apiClient.get<BackendBookshelf>(`/bookshelves/${bookshelfId}`);
  return toBookshelfDto(response.data as BackendBookshelf);
};

/** Create bookshelf (request must include library_id) */
export const createBookshelf = async (request: CreateBookshelfRequest): Promise<BookshelfDto> => {
  const response = await apiClient.post<BackendBookshelf>(`/bookshelves`, request);
  return toBookshelfDto(response.data as BackendBookshelf);
};

/** Update bookshelf */
export const updateBookshelf = async (bookshelfId: string, request: UpdateBookshelfRequest): Promise<BookshelfDto> => {
  const { tagIds, ...rest } = request;
  const payload: Record<string, unknown> = {};

  Object.entries(rest).forEach(([key, value]) => {
    if (typeof value !== 'undefined') {
      payload[key] = value;
    }
  });

  if (typeof tagIds !== 'undefined') {
    payload.tag_ids = tagIds;
  }

  const response = await apiClient.patch<BackendBookshelf>(`/bookshelves/${bookshelfId}`, payload);
  return toBookshelfDto(response.data as BackendBookshelf);
};

/** Delete bookshelf */
export const deleteBookshelf = async (bookshelfId: string): Promise<void> => {
  await apiClient.delete(`/bookshelves/${bookshelfId}`);
};

export const fetchBookshelfDashboard = async (
  options: FetchBookshelfDashboardOptions,
): Promise<BookshelfDashboardPage> => {
  const {
    libraryId,
    page = 1,
    size = 20,
    sort = 'recent_activity',
    statusFilter = 'active',
    fallbackThemeColor,
  } = options;

  if (!libraryId) {
    throw new Error('libraryId is required to load bookshelf dashboard');
  }

  const params = new URLSearchParams();
  params.set('library_id', libraryId);
  params.set('page', String(page));
  params.set('size', String(size));
  params.set('sort', sort);
  params.set('status_filter', statusFilter);

  const { data } = await apiClient.get<BackendBookshelfDashboardResponse>(
    `/bookshelves/dashboard?${params.toString()}`,
  );

  const items = Array.isArray(data.items) ? data.items : [];
  const pageSize = typeof data.page_size === 'number' ? data.page_size : size;
  const total = typeof data.total === 'number' ? data.total : items.length;
  const mapped = items.map((item) => toBookshelfDashboardItem(item, fallbackThemeColor));
  const hasMore = page * pageSize < total;

  const snapshot = normalizeDashboardSnapshot(data.snapshot, mapped);

  return {
    items: mapped,
    total,
    page: typeof data.page === 'number' ? data.page : page,
    page_size: pageSize,
    has_more: hasMore,
    snapshot,
  };
};

const EMPTY_BUCKETS: BookshelfDashboardHealthBuckets = {
  active: 0,
  slowing: 0,
  cooling: 0,
  archived: 0,
};

const countHealthFromItems = (items: BookshelfDashboardItemDto[]): BookshelfDashboardHealthBuckets => {
  return items.reduce<BookshelfDashboardHealthBuckets>((acc, item) => {
    if (typeof acc[item.health] === 'number') {
      acc[item.health] += 1;
    }
    return acc;
  }, { ...EMPTY_BUCKETS });
};

const normalizeBuckets = (
  buckets?: Partial<BookshelfDashboardHealthBuckets> | null,
  fallback?: BookshelfDashboardHealthBuckets,
): BookshelfDashboardHealthBuckets => ({
  active: Math.max(0, buckets?.active ?? fallback?.active ?? 0),
  slowing: Math.max(0, buckets?.slowing ?? fallback?.slowing ?? 0),
  cooling: Math.max(0, buckets?.cooling ?? fallback?.cooling ?? 0),
  archived: Math.max(0, buckets?.archived ?? fallback?.archived ?? 0),
});

const normalizeDashboardSnapshot = (
  snapshot: BackendBookshelfDashboardSnapshot | null | undefined,
  items: BookshelfDashboardItemDto[],
): BookshelfDashboardSnapshot => {
  const derivedHealth = countHealthFromItems(items);
  return {
    total: Math.max(0, snapshot?.total ?? items.length),
    pinned: Math.max(0, snapshot?.pinned ?? items.filter((item) => item.is_pinned).length),
    health: normalizeBuckets(snapshot?.health, derivedHealth),
  };
};
