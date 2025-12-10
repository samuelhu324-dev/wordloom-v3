// src/modules/loom/services/entries.ts — unified + Creation 支持
import { apiFetch } from '@/lib/api';

export type EntryItem = {
  id: number | string;
  src_text?: string; tgt_text?: string;
  src?: string; tgt?: string;
  text?: string; translation?: string;
  source_name?: string; source?: string;
  created_at?: string; updated_at?: string; create_time?: string;
};

export type SearchParams = {
  q?: string;
  source_name?: string;
  sort?: 'created_at' | 'updated_at' | 'id';
  order?: 'asc' | 'desc';
  limit?: number; offset?: number;
};

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };

function withQuery(base: string, params: Record<string, any> = {}) {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return qs ? `${base}?${qs}` : base;
}

async function fetchJSON<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.method && init.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  // apiFetch 已经返回解析后的数据(JSON)，不是Response对象
  return await apiFetch<T>(path, { ...init, headers });
}

function normalizePage<T = EntryItem>(data: any, fallbackLimit = 10, fallbackOffset = 0): Page<T> {
  const items: T[] =
    data?.items ?? data?.results ?? data?.list ?? (Array.isArray(data) ? data : []) ?? [];
  const total =
    data?.total ?? data?.count ?? data?.total_count ?? (Array.isArray(items) ? items.length : 0);
  const limit = data?.limit ?? data?.page_size ?? fallbackLimit;
  const offset = data?.offset ?? data?.page ?? fallbackOffset;
  return { items, total, limit, offset };
}

export async function searchEntries(params: SearchParams = {}): Promise<Page<EntryItem>> {
  // 兼容不同后端挂载路径：优先 /api/common，其次 /api 或 /api/loom
  const paths = ['/api/common/entries/search', '/api/entries/search', '/api/loom/entries/search'];
  let data: any = [];
  let lastErr: any;
  for (const base of paths) {
    const url = withQuery(base, {
      q: params.q,
      source_name: params.source_name,
      limit: params.limit ?? 10,
      offset: params.offset ?? 0,
    });
    try {
      data = await fetchJSON<any>(url);
      lastErr = undefined;
      break;
    } catch (e) {
      lastErr = e;
    }
  }
  if (lastErr) throw lastErr;
  return normalizePage<EntryItem>(data, params.limit ?? 10, params.offset ?? 0);
}

export async function listRecent(limit = 10): Promise<EntryItem[]> {
  const bases = ['/api/common/entries/search', '/api/entries/search', '/api/loom/entries/search'];
  let data: any = [];
  for (const b of bases) {
    try {
      const url = withQuery(b, { limit, q: '', page: 1 });
      data = await fetchJSON<any>(url);
      break;
    } catch {}
  }
  return normalizePage<EntryItem>(data, limit, 0).items;
}

export async function updateEntry(id: number | string, patch: Partial<EntryItem>) {
  const payload: Record<string, any> = {};
  if (typeof patch.src === 'string' && patch.src.trim()) payload.src = patch.src.trim();
  if (typeof patch.tgt === 'string' && patch.tgt.trim()) payload.tgt = patch.tgt.trim();
  if (typeof patch.source_name === 'string') payload.source_name = patch.source_name;
  if (typeof patch.created_at === 'string') payload.created_at = patch.created_at;

  return fetchJSON<EntryItem>(`/api/common/entries/${id}`, {
    method: 'PATCH',
    // 传对象，交给 apiFetch 串行化一次
    body: payload as any,
  });
}
export async function deleteEntry(id: number | string) {
  await fetchJSON<void>(`/api/common/entries/${id}`, { method: 'DELETE' });
}

export type BatchInsertItem = {
  text?: string;
  translation?: string;
  direction?: 'zh>en' | 'en>zh';
  source_name?: string;
  source_id?: string | number;
  ts_iso?: string;
};

export async function batchInsert(entries: BatchInsertItem[]): Promise<Response> {
  // 将前端的数据结构转换为后端期望的格式
  const items = entries.map(e => {
    const isEnToZh = e.direction === 'en>zh';
    return {
      src: isEnToZh ? (e.text || '') : (e.translation || ''),
      tgt: isEnToZh ? (e.translation || '') : (e.text || ''),
      lang_src: isEnToZh ? 'en' : 'zh',
      lang_tgt: isEnToZh ? 'zh' : 'en',
      article_id: null,
      position: 0,
      created_at: e.ts_iso,
      source_name: e.source_name,
    };
  });

  return apiFetch('/api/common/entries/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // 传对象，apiFetch 会 stringify 一次
    body: { items } as any,
  }) as any;
}
