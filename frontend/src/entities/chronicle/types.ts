import { BaseDto } from '@/shared/api';

export type ChronicleEventType =
  | 'book_created'
  | 'book_moved'
  | 'book_moved_to_basement'
  | 'book_restored'
  | 'book_deleted'
  | 'block_status_changed'
  | 'book_opened'
  | 'book_viewed'
  | 'book_stage_changed'
  | 'book_maturity_recomputed'
  | 'structure_task_completed'
  | 'structure_task_regressed'
  | 'book_soft_deleted'
  | 'cover_changed'
  | 'cover_color_changed'
  | 'content_snapshot_taken'
  | 'wordcount_milestone_reached'
  | 'todo_promoted_from_block'
  | 'todo_completed'
  | 'work_session_summary'
  | 'focus_started'
  | 'focus_ended';

export interface ChronicleEventDto extends BaseDto {
  event_type: ChronicleEventType;
  book_id: string;
  block_id?: string | null;
  actor_id?: string | null;
  payload: Record<string, unknown>;
  occurred_at: string;
}

export interface BackendChronicleEvent {
  id: string;
  event_type: ChronicleEventType;
  book_id: string;
  block_id?: string | null;
  actor_id?: string | null;
  payload?: Record<string, unknown> | null;
  occurred_at: string;
  created_at?: string | null;
}

export interface ChronicleTimelinePage {
  items: ChronicleEventDto[];
  total: number;
  page: number;
  size: number;
  has_more: boolean;
}

export const toChronicleEventDto = (event: BackendChronicleEvent): ChronicleEventDto => {
  const createdAt = event.created_at || event.occurred_at || new Date().toISOString();
  return {
    id: event.id,
    event_type: event.event_type,
    book_id: event.book_id,
    block_id: event.block_id || null,
    actor_id: event.actor_id || null,
    payload: event.payload || {},
    occurred_at: event.occurred_at,
    created_at: createdAt,
    updated_at: createdAt,
  };
};
