// Removed 'use client' to allow server-side usage for SSR prefetch

import { api, apiClient, buildMediaFileUrl } from '@/shared/api';
import { CreateLibraryRequest, LibraryDto, LibraryTagSummaryDto, UpdateLibraryRequest } from '@/entities/library';

const BASE_URL = '/libraries';

// 简单的 in-flight 请求去重，防止在开发模式 StrictMode 双渲染或重复调用导致二次 /libraries 请求
const inflight: Partial<Record<string, Promise<LibraryDto[]>>> = {};

export type LibrarySortOption = 'last_activity' | 'created' | 'name' | 'views';

interface ListLibrariesParams {
  query?: string;
  sort?: LibrarySortOption;
  includeArchived?: boolean;
}

/** List libraries (optional search) with 3s timeout + fallback cache (stale-while-revalidate) */
export async function listLibraries(params?: ListLibrariesParams): Promise<LibraryDto[]> {
  const cacheKey = JSON.stringify({
    query: (params?.query || '').trim().toLowerCase(),
    sort: params?.sort || 'last_activity',
    includeArchived: Boolean(params?.includeArchived),
  });
  if (inflight[cacheKey]) return inflight[cacheKey];

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000); // 3 秒硬超时

  const q = params?.query?.trim();
  const searchParams = new URLSearchParams();
  if (q) searchParams.set('query', q);
  if (params?.sort) searchParams.set('sort', params.sort);
  if (params?.includeArchived) searchParams.set('include_archived', 'true');

  const url = searchParams.toString() ? `${BASE_URL}?${searchParams.toString()}` : BASE_URL;
  const p = api.get<any>(url, { signal: controller.signal })
    .then((response) => {
      const data = response.data;
      if (Array.isArray(data)) return data as LibraryDto[];
      if (data && Array.isArray(data.items)) return data.items as LibraryDto[];
      return [];
    })
    .then((arr) => {
      const decorated = decorateLibraries(arr);
      // 存入缓存供下次首屏使用
      try {
        localStorage.setItem(
          'wl_libraries_cache',
          JSON.stringify({
            ts: Date.now(),
            data: decorated,
            query: q || '',
            sort: params?.sort || 'last_activity',
            includeArchived: Boolean(params?.includeArchived),
          })
        );
      } catch (_) {}
      return decorated;
    })
    .catch((err) => {
      // 超时或网络失败 → 使用缓存回退（若存在），并在控制台标记
      if (controller.signal.aborted) {
        try {
          const raw = localStorage.getItem('wl_libraries_cache');
          if (raw) {
            const parsed = JSON.parse(raw);
            const sameQuery = (parsed.query || '') === (q || '');
            const sameSort = (parsed.sort || 'last_activity') === (params?.sort || 'last_activity');
            const sameArchived = Boolean(parsed.includeArchived) === Boolean(params?.includeArchived);
            if (sameQuery && sameSort && sameArchived) {
              console.warn('[libraries] 使用缓存回退 (请求超时 >3s)');
              return decorateLibraries(parsed.data as LibraryDto[]);
            }
          }
        } catch (_) {}
      }
      throw err;
    })
    .finally(() => {
      clearTimeout(timeout);
      delete inflight[cacheKey];
    });

  inflight[cacheKey] = p;
  return p;
}

/** Get library by ID with 3s timeout + localStorage cache fallback */
export async function getLibrary(id: string): Promise<LibraryDto> {
  const cacheKey = `wl_library_cache_${id}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000); // 3s hard timeout
  try {
    const response = await api.get<LibraryDto>(`${BASE_URL}/${id}`, { signal: controller.signal });
    const data = decorateLibrary(response.data as LibraryDto);
    // store fresh value
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), data }));
      }
    } catch (_) {}
    return data;
  } catch (err: any) {
    // timeout or network error → fallback to cache if available
    if (controller.signal.aborted) {
      try {
        if (typeof window !== 'undefined') {
          const raw = localStorage.getItem(cacheKey);
          if (raw) {
            const parsed = JSON.parse(raw);
            console.warn(`[library:${id}] 使用缓存回退 (请求超时 >3s)`);
            return decorateLibrary(parsed.data as LibraryDto);
          }
        }
      } catch (_) {}
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

/** Create new library */
export async function createLibrary(request: CreateLibraryRequest): Promise<LibraryDto> {
  const response = await api.post<any>(BASE_URL, request);
  return decorateLibrary(response.data as LibraryDto);
}

/** Update library */
export async function updateLibrary(
  id: string,
  request: Partial<UpdateLibraryRequest>
): Promise<LibraryDto> {
  const response = await api.patch<LibraryDto>(`${BASE_URL}/${id}`, request);
  return decorateLibrary(response.data as LibraryDto);
}

/** Delete library */
export async function deleteLibrary(id: string): Promise<void> {
  await api.delete(`${BASE_URL}/${id}`);
}

/** Record a library view (increment counters) */
export async function recordLibraryView(libraryId: string): Promise<LibraryDto> {
  const response = await api.post<LibraryDto>(`${BASE_URL}/${libraryId}/views`);
  return decorateLibrary(response.data as LibraryDto);
}

/** Upload library cover via multipart form data */
export async function uploadLibraryCover(libraryId: string, file: File): Promise<LibraryDto> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<LibraryDto>(`${BASE_URL}/${libraryId}/cover`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return decorateLibrary(response.data as LibraryDto);
}

export interface LibraryTagsResponseDto {
  library_id: string;
  tag_ids: string[];
  tags: LibraryTagSummaryDto[];
  tag_total_count: number;
}

export async function getLibraryTags(libraryId: string, limit = 25): Promise<LibraryTagsResponseDto> {
  const response = await api.get<LibraryTagsResponseDto>(`${BASE_URL}/${libraryId}/tags`, {
    params: { limit },
  });
  return normalizeLibraryTagsResponse(response.data);
}

export async function replaceLibraryTags(
  libraryId: string,
  tagIds: string[],
  limit = 25
): Promise<LibraryTagsResponseDto> {
  const response = await api.put<LibraryTagsResponseDto>(
    `${BASE_URL}/${libraryId}/tags`,
    { tag_ids: tagIds },
    { params: { limit } }
  );
  return normalizeLibraryTagsResponse(response.data);
}

function normalizeLibraryTagsResponse(payload: LibraryTagsResponseDto): LibraryTagsResponseDto {
  const tagIds = Array.isArray(payload.tag_ids) ? payload.tag_ids : [];
  const tags = Array.isArray(payload.tags) ? payload.tags : [];
  const tagTotalCount =
    typeof payload.tag_total_count === 'number'
      ? payload.tag_total_count
      : (tagIds.length || tags.length || 0);

  return {
    library_id: payload.library_id,
    tag_ids: tagIds,
    tags,
    tag_total_count: tagTotalCount,
  };
}

function decorateLibraries(items: LibraryDto[]): LibraryDto[] {
  return items.map((item) => decorateLibrary(item));
}

function decorateLibrary(library: LibraryDto): LibraryDto {
  if (!library) return library;
  const tags = Array.isArray(library.tags) ? library.tags : [];
  const tagTotal = typeof library.tag_total_count === 'number' ? library.tag_total_count : tags.length;
  const normalized: LibraryDto = {
    ...library,
    tags,
    tag_total_count: tagTotal,
  };

  if (!normalized.cover_media_id) {
    return { ...normalized, coverUrl: undefined };
  }

  const cacheKey = normalized.updated_at || Date.now().toString();
  return {
    ...normalized,
    coverUrl: buildMediaFileUrl(normalized.cover_media_id, cacheKey),
  };
}
