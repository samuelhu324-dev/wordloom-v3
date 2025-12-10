import { apiClient } from '@/shared/api';
import type { BookMaturity } from '@/entities/book';

const clampScore = (value?: number | null): number => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  return Math.min(100, Math.max(0, Math.round(value)));
};

const normalizeStage = (stage?: string | null): BookMaturity => {
  const lowered = typeof stage === 'string' ? stage.toLowerCase() : 'seed';
  if (lowered === 'growing' || lowered === 'stable' || lowered === 'legacy') {
    return lowered;
  }
  return 'seed';
};

export interface BackendMaturityScoreComponent {
  factor?: string;
  points?: number;
  detail?: string;
}

export interface BackendTransitionTask {
  code?: string;
  title?: string;
  description?: string;
  weight?: number;
  required_stage?: string | null;
  status?: string | null;
}

export interface BackendMaturitySnapshot {
  book_id: string;
  stage?: string | null;
  score?: {
    value?: number | null;
    components?: BackendMaturityScoreComponent[];
  } | null;
  tasks?: BackendTransitionTask[] | null;
  created_at?: string | null;
  manual_override?: boolean | null;
  manual_reason?: string | null;
  blocks_count?: number | null;
  block_type_count?: number | null;
  todos_count?: number | null;
  tags_count?: number | null;
  visits_90d?: number | null;
  summary_length?: number | null;
  has_title?: boolean | null;
  has_summary?: boolean | null;
  has_cover_icon?: boolean | null;
  operations_bonus?: number | null;
  last_visit_at?: string | null;
  last_event_at?: string | null;
}

export interface MaturityScoreComponentDto {
  factor: string;
  points: number;
  detail: string;
}

export interface MaturityScoreDto {
  value: number;
  components: MaturityScoreComponentDto[];
}

export type TransitionTaskStatus = 'locked' | 'pending' | 'completed' | 'regressed';

export interface TransitionTaskDto {
  code: string;
  title: string;
  description: string;
  weight: number;
  requiredStage: BookMaturity;
  status: TransitionTaskStatus;
}

export interface MaturitySnapshotDto {
  bookId: string;
  stage: BookMaturity;
  score: MaturityScoreDto;
  tasks: TransitionTaskDto[];
  createdAt: string;
  manualOverride: boolean;
  manualReason?: string;
  blocksCount: number;
  blockTypeCount: number;
  todosCount: number;
  tagsCount: number;
  visits90d: number;
  summaryLength: number;
  hasTitle: boolean;
  hasSummary: boolean;
  hasCoverIcon: boolean;
  operationsBonus: number;
  lastVisitAt?: string | null;
  lastEventAt?: string | null;
}

const normalizeScoreComponents = (
  components?: BackendMaturityScoreComponent[] | null,
): MaturityScoreComponentDto[] => {
  if (!Array.isArray(components)) {
    return [];
  }
  return components.map((component, index) => ({
    factor: component?.factor || `component_${index + 1}`,
    points: typeof component?.points === 'number' && Number.isFinite(component.points)
      ? component.points
      : 0,
    detail: component?.detail || '—',
  }));
};

const normalizeTaskStatus = (status?: string | null): TransitionTaskStatus => {
  const normalized = typeof status === 'string' ? status.toLowerCase() : '';
  switch (normalized) {
    case 'locked':
    case 'completed':
    case 'regressed':
      return normalized;
    case 'pending':
    default:
      return 'pending';
  }
};

const normalizeTasks = (tasks?: BackendTransitionTask[] | null): TransitionTaskDto[] => {
  if (!Array.isArray(tasks)) {
    return [];
  }
  return tasks.map((task, index) => ({
    code: task?.code || `task_${index + 1}`,
    title: task?.title || '未命名任务',
    description: task?.description || '暂无描述',
    weight: typeof task?.weight === 'number' && Number.isFinite(task.weight)
      ? task.weight
      : 1,
    requiredStage: normalizeStage(task?.required_stage),
    status: normalizeTaskStatus(task?.status),
  }));
};

export const normalizeMaturitySnapshot = (snapshot: BackendMaturitySnapshot): MaturitySnapshotDto => {
  const stage = normalizeStage(snapshot.stage);
  const scoreValue = clampScore(snapshot.score?.value ?? null);
  const components = normalizeScoreComponents(snapshot.score?.components);
  const tasks = normalizeTasks(snapshot.tasks);
  const createdAt = typeof snapshot.created_at === 'string' && snapshot.created_at
    ? snapshot.created_at
    : new Date().toISOString();
  const manualReason = typeof snapshot.manual_reason === 'string' && snapshot.manual_reason.trim().length > 0
    ? snapshot.manual_reason.trim()
    : undefined;

  return {
    bookId: snapshot.book_id,
    stage,
    score: {
      value: scoreValue,
      components,
    },
    tasks,
    createdAt,
    manualOverride: Boolean(snapshot.manual_override),
    manualReason,
    blocksCount: typeof snapshot.blocks_count === 'number' ? snapshot.blocks_count : 0,
    blockTypeCount: typeof snapshot.block_type_count === 'number' ? snapshot.block_type_count : 0,
    todosCount: typeof snapshot.todos_count === 'number' ? snapshot.todos_count : 0,
    tagsCount: typeof snapshot.tags_count === 'number' ? snapshot.tags_count : 0,
    visits90d: typeof snapshot.visits_90d === 'number' ? snapshot.visits_90d : 0,
    summaryLength: typeof snapshot.summary_length === 'number' ? snapshot.summary_length : 0,
    hasTitle: Boolean(snapshot.has_title),
    hasSummary: Boolean(snapshot.has_summary),
    hasCoverIcon: Boolean(snapshot.has_cover_icon),
    operationsBonus: typeof snapshot.operations_bonus === 'number' ? snapshot.operations_bonus : 0,
    lastVisitAt: snapshot.last_visit_at ?? null,
    lastEventAt: snapshot.last_event_at ?? null,
  };
};

export const listBookMaturitySnapshots = async (
  bookId: string,
  limit: number = 5,
): Promise<MaturitySnapshotDto[]> => {
  if (!bookId) {
    return [];
  }
  const safeLimit = Math.max(1, limit);
  const query = new URLSearchParams({ limit: String(safeLimit) }).toString();
  const response = await apiClient.get<BackendMaturitySnapshot[]>(
    `/maturity/books/${bookId}/snapshots?${query}`,
  );
  const payload = Array.isArray(response.data) ? response.data : [];
  return payload.map(normalizeMaturitySnapshot);
};
