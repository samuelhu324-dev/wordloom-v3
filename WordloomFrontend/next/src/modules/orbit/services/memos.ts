// next/src/modules/orbit/services/memos.ts
import { ORBIT_API_BASE } from '@/lib/apiBase';
import type { Memo } from '@/modules/orbit/domain/types';
// 统一 HTTP 调用：默认 JSON
async function http<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.method && init.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  const res = await fetch(url, { ...init, headers, next: { revalidate: 0 } });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || res.statusText);
  }
  // 204 无内容
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}


export interface ListMemoParams {
  q?: string;
  order_by?: 'created_at' | 'updated_at';
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

function withQuery(base: string, params: Record<string, any> = {}) {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return qs ? `${base}?${qs}` : base;
}

export async function listMemos(params: ListMemoParams = {}): Promise<Memo[]> {
  const url = withQuery(`${ORBIT_API_BASE}/memos`, params);
  return await http<Memo[]>(url);
}

export interface CreateMemoInput {
  text: string;
  tags?: string;
  linked_source_id?: number;
  linked_entry_id?: number;
}

export async function createMemo(input: CreateMemoInput): Promise<Memo> {
  return await http<Memo>(`${ORBIT_API_BASE}/memos`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export type UpdateMemoInput = Partial<CreateMemoInput>;

export async function updateMemo(id: number, patch: UpdateMemoInput): Promise<Memo> {
  return await http<Memo>(`${ORBIT_API_BASE}/memos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}

export async function deleteMemo(id: number): Promise<void> {
  await http<void>(`${ORBIT_API_BASE}/memos/${id}`, { method: 'DELETE' });
}
