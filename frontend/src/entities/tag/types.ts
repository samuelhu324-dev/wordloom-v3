import { BaseDto } from '@/shared/api';

/** Tag DTO - 全局标签 */
export interface TagDto extends BaseDto {
  name: string;
  color: string;
  icon?: string | null;
  description?: string | null;
  parent_tag_id?: string | null;
  level: number;
  usage_count: number;
  deleted_at?: string | null;
}

/** Create Tag Request */
export interface CreateTagRequest {
  name: string;
  color: string;
  parent_id?: string;
  description?: string | null;
  icon?: string | null;
  parent_tag_id?: string | null;
}

/** Update Tag Request */
export interface UpdateTagRequest {
  name?: string;
  color?: string;
  parent_id?: string;
  description?: string | null;
  icon?: string | null;
}
