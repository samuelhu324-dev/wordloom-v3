import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { ChronicleEventType, ChronicleTimelinePage } from '@/entities/chronicle';
import { listChronicleEvents } from './api';

export const CHRONICLE_QUERY_KEY = {
  all: ['chronicle'] as const,
  timeline: (bookId: string, filters?: { eventTypes?: ChronicleEventType[]; size?: number }) =>
    [...CHRONICLE_QUERY_KEY.all, { bookId, filters }] as const,
  recent: (bookId: string, filters?: { eventTypes?: ChronicleEventType[]; limit?: number }) =>
    [...CHRONICLE_QUERY_KEY.all, 'recent', { bookId, filters }] as const,
} as const;

export const CHRONICLE_DEFAULT_EVENT_TYPES: ChronicleEventType[] = [
  'book_created',
  'book_moved',
  'book_moved_to_basement',
  'book_soft_deleted',
  'book_restored',
  'book_deleted',
  'book_renamed',
  'book_updated',
  'block_created',
  'block_updated',
  'block_soft_deleted',
  'block_restored',
  'block_type_changed',
  'block_status_changed',
  'book_stage_changed',
  'book_maturity_recomputed',
  'structure_task_completed',
  'structure_task_regressed',
  'cover_changed',
  'cover_color_changed',
  'content_snapshot_taken',
  'wordcount_milestone_reached',
  'todo_promoted_from_block',
  'todo_completed',
  'tag_added_to_book',
  'tag_removed_from_book',
];

export interface UseChronicleTimelineOptions {
  pageSize?: number;
  eventTypes?: ChronicleEventType[];
}

export const useChronicleTimeline = (
  bookId: string,
  { pageSize = 20, eventTypes }: UseChronicleTimelineOptions = {}
) => {
  return useInfiniteQuery<ChronicleTimelinePage>({
    queryKey: CHRONICLE_QUERY_KEY.timeline(bookId, { eventTypes, size: pageSize }),
    queryFn: ({ pageParam }) => {
      const page = typeof pageParam === 'number' ? pageParam : 1;
      return listChronicleEvents({ bookId, page, size: pageSize, eventTypes });
    },
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.page + 1 : undefined),
    enabled: Boolean(bookId),
    staleTime: 1000 * 60,
    initialPageParam: 1,
    placeholderData: (previous) => previous,
  });
};

export interface UseRecentChronicleEventsOptions {
  limit?: number;
  eventTypes?: ChronicleEventType[];
}

export const useRecentChronicleEvents = (
  bookId: string,
  { limit = 5, eventTypes }: UseRecentChronicleEventsOptions = {}
) => {
  const resolvedEventTypes = eventTypes ?? CHRONICLE_DEFAULT_EVENT_TYPES;

  return useQuery<ChronicleTimelinePage>({
    queryKey: CHRONICLE_QUERY_KEY.recent(bookId, { eventTypes: resolvedEventTypes, limit }),
    queryFn: () => listChronicleEvents({ bookId, page: 1, size: limit, eventTypes: resolvedEventTypes }),
    enabled: Boolean(bookId),
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 5,
  });
};
