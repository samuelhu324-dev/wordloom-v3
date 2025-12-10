import { BaseDto } from '@/shared/api';

/** Media DTO - 媒体资源 */
export interface MediaDto extends BaseDto {
  path: string;
  media_type: 'IMAGE' | 'VIDEO' | 'AUDIO' | 'DOCUMENT';
  size_bytes: number;
  mime_type: string;
  trashed_at?: string;
  purge_at?: string;
}

/** Create Media Request (upload) */
export interface CreateMediaRequest {
  file: File;
  media_type: MediaDto['media_type'];
}

/** Delete Media Request */
export interface DeleteMediaRequest {
  media_id: string;
}
