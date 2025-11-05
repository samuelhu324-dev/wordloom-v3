/**
 * Media Resource 类型定义和 API 客户端
 */

// ============================================================================
// 类型定义
// ============================================================================

export enum MediaEntityType {
  BOOKSHELF_COVER = 'bookshelf_cover',
  NOTE_COVER = 'note_cover',
  CHECKPOINT_MARKER = 'checkpoint_marker',
  IMAGE_BLOCK = 'image_block',
  OTHER_BLOCK = 'other_block',
}

/**
 * 统一的媒体资源类型
 */
export interface MediaResource {
  id: string;
  workspace_id: string;
  entity_type: MediaEntityType;
  entity_id: string;
  file_name: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
  width?: number;
  height?: number;
  display_order: number;
  is_thumbnail: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * 创建媒体资源的请求
 */
export interface CreateMediaResourceRequest {
  workspace_id: string;
  entity_type: MediaEntityType;
  entity_id: string;
  display_order?: number;
}

/**
 * 重新排列媒体资源的请求
 */
export interface ReorderMediaResourceRequest {
  entity_id: string;
  entity_type: MediaEntityType;
  order: string[]; // media_id 列表
}

// ============================================================================
// API 客户端函数
// ============================================================================

const API_BASE = '/api/orbit/media';

/**
 * 上传媒体资源
 */
export async function uploadMedia(
  file: File,
  workspace_id: string,
  entity_type: MediaEntityType,
  entity_id: string,
  display_order: number = 0
): Promise<MediaResource> {
  const formData = new FormData();
  formData.append('file', file);

  // 构建 URL 查询参数
  const params = new URLSearchParams({
    workspace_id,
    entity_type,
    entity_id,
    display_order: display_order.toString(),
  });

  console.log('[uploadMedia] Uploading to:', `${API_BASE}/upload?${params.toString()}`);

  const response = await fetch(`${API_BASE}/upload?${params.toString()}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[uploadMedia] Error response:', errorText);
    throw new Error(`Failed to upload media: ${response.statusText} - ${errorText}`);
  }

  const data = await response.json();
  console.log('[uploadMedia] Success:', data);
  return data;
}

/**
 * 获取实体的所有媒体资源
 */
export async function getMediaByEntity(
  entity_type: MediaEntityType,
  entity_id: string
): Promise<MediaResource[]> {
  const params = new URLSearchParams({
    entity_type,
    entity_id,
  });

  const response = await fetch(`${API_BASE}?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch media: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 获取单个媒体资源
 */
export async function getMedia(media_id: string): Promise<MediaResource> {
  const response = await fetch(`${API_BASE}/${media_id}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch media: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 删除媒体资源
 */
export async function deleteMedia(media_id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${media_id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete media: ${response.statusText}`);
  }
}

/**
 * 重新排列媒体资源
 */
export async function reorderMedia(
  payload: ReorderMediaResourceRequest
): Promise<void> {
  const response = await fetch(`${API_BASE}/reorder`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to reorder media: ${response.statusText}`);
  }
}
