import { BaseDto } from '@/shared/api';

/** Library DTO - 用户的数据容器 */
export interface LibraryDto extends BaseDto {
  user_id: string;
  name: string;
  description?: string;
  basement_bookshelf_id?: string;
}

/** Create Library Request */
export interface CreateLibraryRequest {
  name: string;
  description?: string;
}

/** Update Library Request */
export interface UpdateLibraryRequest {
  name?: string;
  description?: string;
}
