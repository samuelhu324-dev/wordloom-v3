// next/src/modules/orbit/services/stats.ts
import { ORBIT_API_BASE } from '@/lib/apiBase';
import type { Stat } from '@/modules/orbit/domain/types';
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


export async function listStats(): Promise<Stat[]> {
  return await http<Stat[]>(`${ORBIT_API_BASE}/stats`);
}

export async function upsertStat(metric: string, value: number): Promise<Stat> {
  return await http<Stat>(`${ORBIT_API_BASE}/stats`, {
    method: 'POST',
    body: JSON.stringify({ metric, value }),
  });
}
