import { BaseDto } from '@/shared/api';

/** Tag DTO - 全局标签 */
export interface TagDto extends BaseDto {
  name: string;
  color?: string;
  parent_id?: string;
}

/** Create Tag Request */
export interface CreateTagRequest {
  name: string;
  color?: string;
  parent_id?: string;
}

/** Update Tag Request */
export interface UpdateTagRequest {
  name?: string;
  color?: string;
  parent_id?: string;
}
