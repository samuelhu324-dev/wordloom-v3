import { apiClient } from '@/shared/api';
import {
  ChronicleTimelinePage,
  BackendChronicleEvent,
  ChronicleEventDto,
  ChronicleEventType,
  toChronicleEventDto,
} from '@/entities/chronicle';

interface BackendChronicleListResponse {
  items: BackendChronicleEvent[];
  total: number;
  page: number;
  size: number;
  has_more: boolean;
}

export interface ChronicleTimelineParams {
  bookId: string;
  page?: number;
  size?: number;
  eventTypes?: ChronicleEventType[];
}

const buildQuery = ({ page = 1, size = 20, eventTypes }: Pick<ChronicleTimelineParams, 'page' | 'size' | 'eventTypes'>): string => {
  const search = new URLSearchParams();
  search.set('page', String(page));
  search.set('size', String(size));
  eventTypes?.forEach((type) => {
    search.append('event_types', type);
  });
  const query = search.toString();
  return query ? `?${query}` : '';
};

export const listChronicleEvents = async ({
  bookId,
  page = 1,
  size = 20,
  eventTypes,
}: ChronicleTimelineParams): Promise<ChronicleTimelinePage> => {
  if (!bookId) {
    return { items: [], total: 0, page: 1, size, has_more: false };
  }
  const query = buildQuery({ page, size, eventTypes });
  const { data } = await apiClient.get<BackendChronicleListResponse>(
    `/chronicle/books/${bookId}/events${query}`
  );
  const normalized: ChronicleTimelinePage = {
    items: (data.items || []).map<ChronicleEventDto>(toChronicleEventDto),
    total: data.total ?? 0,
    page: data.page ?? page,
    size: data.size ?? size,
    has_more: Boolean(
      data.has_more ?? ((page - 1) * size + (data.items?.length ?? 0)) < (data.total ?? 0)
    ),
  };
  return normalized;
};
