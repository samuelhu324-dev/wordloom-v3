/**
 * Orbit Query Keys
 * ----------------
 * 统一的 React Query key 工厂，避免与 Loom 的 key 冲突。
 * 使用方式：useQuery(orbitKeys.tasks.list({ status: 'doing' }), fetcher)
 */

export type TaskFilters = {
  q?: string;
  status?: 'todo' | 'doing' | 'done' | 'archived';
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  domain?: 'dev' | 'translate' | 'research' | 'study';
};

export const orbitKeys = {
  all: ['orbit'] as const,

  tasks: {
    all: () => [...orbitKeys.all, 'tasks'] as const,
    list: (filters?: TaskFilters) =>
      [...orbitKeys.tasks.all(), { filters: filters ?? {} }] as const,
    detail: (id: number) =>
      [...orbitKeys.tasks.all(), 'detail', id] as const,
  },

  memos: {
    all: () => [...orbitKeys.all, 'memos'] as const,
    list: (q?: string) =>
      [...orbitKeys.memos.all(), { q: q ?? '' }] as const,
    detail: (id: number) =>
      [...orbitKeys.memos.all(), 'detail', id] as const,
  },

  stats: {
    all: () => [...orbitKeys.all, 'stats'] as const,
    summary: () => [...orbitKeys.stats.all(), 'summary'] as const,
  },
} as const;

export type OrbitKey =
  | ReturnType<typeof orbitKeys.tasks.all>
  | ReturnType<typeof orbitKeys.tasks.list>
  | ReturnType<typeof orbitKeys.tasks.detail>
  | ReturnType<typeof orbitKeys.memos.all>
  | ReturnType<typeof orbitKeys.memos.list>
  | ReturnType<typeof orbitKeys.memos.detail>
  | ReturnType<typeof orbitKeys.stats.all>
  | ReturnType<typeof orbitKeys.stats.summary>;
