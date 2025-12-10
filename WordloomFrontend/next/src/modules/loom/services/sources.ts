// src/modules/loom/services/sources.ts
import { apiFetch } from '@/lib/api';

export type SourceOption = { id?: number | string; name: string };

async function fetchJSON<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.method && init.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  // apiFetch 已经返回解析后的数据(JSON)，不是Response对象
  return await apiFetch<T>(path, { ...init, headers });
}

export async function listSources(): Promise<SourceOption[]> {
  // 兼容不同后端挂载路径：优先 /api/common，其次 /api 或 /api/loom
  const candidates = ['/api/common/sources', '/api/sources', '/api/loom/sources'];
  let data: any = [];
  let lastErr: any;
  for (const p of candidates) {
    try {
      data = await apiFetch<any>(p, { headers: { accept: 'application/json' } });
      lastErr = undefined;
      break;
    } catch (e) {
      lastErr = e;
    }
  }
  if (lastErr) throw lastErr;
  const toOpt = (x: any): SourceOption =>
    typeof x === 'string' ? { name: x } : { name: x?.name ?? String(x), id: x?.id };
  if (Array.isArray(data)) return data.map(toOpt);
  if (Array.isArray(data?.items)) return data.items.map(toOpt);
  return [];
}

export async function renameSource(oldName: string, newName: string) {
  await fetchJSON('/api/common/sources/rename', {
    method: 'POST',
    body: JSON.stringify({ old_name: oldName, new_name: newName }),
  });
  return { ok: true as const };
}
