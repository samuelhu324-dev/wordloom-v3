/**
 * Checkpoint 相关类型和 API 客户端函数
 */

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 检查点标记的图片对象
 */
export interface CheckpointMarkerImage {
  url: string; // 图片 URL
}

/**
 * 检查点标记（进度标记）
 */
export interface CheckpointMarker {
  id: string;
  checkpoint_id: string;
  title: string;
  description?: string;
  started_at: string; // ISO 8601 datetime
  ended_at: string; // ISO 8601 datetime
  duration_seconds: number;
  category: string; // work, pause, bug, feature, review, custom
  tags: string[]; // tag IDs
  color: string; // hex color, e.g., "#3b82f6"
  emoji: string; // emoji character, e.g., "✓"
  order: number;
  is_completed: boolean; // 是否已完成
  image_urls?: CheckpointMarkerImage[]; // 图片列表（最多 5 张，每张 60x60）
  created_at: string; // ISO 8601 datetime
}

/**
 * 检查点（子事项）- 基础版本
 */
export interface Checkpoint {
  id: string;
  note_id: string;
  title: string;
  description?: string;
  status: string; // pending, in_progress, on_hold, done
  tags: string[]; // tag IDs
  order: number;
  created_at: string; // ISO 8601 datetime
  started_at?: string; // ISO 8601 datetime
  completed_at?: string; // ISO 8601 datetime
  duration_seconds: number;
  actual_work_seconds: number;
  completion_percentage: number;
}

/**
 * 检查点详情（包含所有 marker）
 */
export interface CheckpointDetail extends Checkpoint {
  markers: CheckpointMarker[];
}

/**
 * 创建检查点的请求
 */
export interface CreateCheckpointRequest {
  title: string;
  description?: string;
  status?: string;
  tags?: string[];
  order?: number;
}

/**
 * 更新检查点的请求
 */
export interface UpdateCheckpointRequest {
  title?: string;
  description?: string;
  status?: string;
  tags?: string[];
  order?: number;
}

/**
 * 创建标记的请求
 */
export interface CreateCheckpointMarkerRequest {
  title: string;
  description?: string;
  started_at: string; // ISO 8601 datetime
  ended_at: string; // ISO 8601 datetime
  category?: string;
  tags?: string[];
  color?: string;
  emoji?: string;
  order?: number;
  is_completed?: boolean;
  image_urls?: CheckpointMarkerImage[]; // 图片列表
}

/**
 * 更新标记的请求
 */
export interface UpdateCheckpointMarkerRequest {
  title?: string;
  description?: string;
  started_at?: string;
  ended_at?: string;
  category?: string;
  tags?: string[];
  color?: string;
  emoji?: string;
  order?: number;
  is_completed?: boolean;
  image_urls?: CheckpointMarkerImage[]; // 图片列表
}

/**
 * 检查点统计信息
 */
export interface CheckpointStats {
  checkpoint_id: string;
  total_duration_seconds: number;
  actual_work_seconds: number;
  pause_duration_seconds: number;
  marker_count: number;
  completion_percentage: number;
  status: string;
}

// ============================================================================
// API 客户端函数
// ============================================================================

const API_BASE = "/api/orbit/checkpoints";

/**
 * 为 note 创建新检查点
 */
export async function createCheckpoint(
  noteId: string,
  data: CreateCheckpointRequest
): Promise<Checkpoint> {
  const response = await fetch(`${API_BASE}?note_id=${noteId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to create checkpoint: ${response.statusText}`);
  return response.json();
}

/**
 * 获取单个检查点详情（包含所有 marker）
 */
export async function getCheckpoint(checkpointId: string): Promise<CheckpointDetail> {
  const response = await fetch(`${API_BASE}/${checkpointId}`);
  if (!response.ok) throw new Error(`Failed to fetch checkpoint: ${response.statusText}`);
  return response.json();
}

/**
 * 更新检查点
 */
export async function updateCheckpoint(
  checkpointId: string,
  data: UpdateCheckpointRequest
): Promise<Checkpoint> {
  const response = await fetch(`${API_BASE}/${checkpointId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to update checkpoint: ${response.statusText}`);
  return response.json();
}

/**
 * 删除检查点
 */
export async function deleteCheckpoint(checkpointId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${checkpointId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(`Failed to delete checkpoint: ${response.statusText}`);
}

/**
 * 获取某个 note 的所有检查点
 */
export async function listCheckpoints(noteId: string): Promise<CheckpointDetail[]> {
  const url = `${API_BASE}/note/${noteId}/all`;
  console.log('[Checkpoints API] Fetching checkpoints:', { url, noteId });

  try {
    const response = await fetch(url);

    console.log('[Checkpoints API] Response status:', response.status, response.statusText);

    if (!response.ok) {
      // 尝试解析错误响应
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        console.error('[Checkpoints API] Error response:', errorData);
        if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch {
        // 如果响应不是 JSON，使用状态文本
        console.error('[Checkpoints API] Response is not JSON, status:', response.statusText);
      }

      // 诊断信息
      if (response.status === 404) {
        console.error('[Checkpoints API] ⚠️ 404 Not Found - API 端点不存在！可能原因：');
        console.error('  1. 后端服务未启动（http://localhost:8012）');
        console.error('  2. 路由未正确注册在 main_orbit.py 中');
        console.error('  3. 检查 app/routers/orbit/checkpoints.py 是否存在');
      }

      throw new Error(`Failed to fetch checkpoints: ${errorMessage}`);
    }

    const data = await response.json();
    console.log('[Checkpoints API] Successfully fetched checkpoints:', { count: data.length });
    return data;
  } catch (error) {
    console.error('[Checkpoints API] Fetch failed:', error);
    throw error;
  }
}

/**
 * 获取检查点统计信息
 */
export async function getCheckpointStats(checkpointId: string): Promise<CheckpointStats> {
  const response = await fetch(`${API_BASE}/${checkpointId}/stats`);
  if (!response.ok) throw new Error(`Failed to fetch checkpoint stats: ${response.statusText}`);
  return response.json();
}

// ============================================================================
// Marker API 函数
// ============================================================================

/**
 * 为检查点添加标记
 */
export async function createCheckpointMarker(
  checkpointId: string,
  data: CreateCheckpointMarkerRequest
): Promise<CheckpointMarker> {
  const response = await fetch(`${API_BASE}/${checkpointId}/markers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to create marker: ${response.statusText}`);
  return response.json();
}

/**
 * 获取检查点的所有标记
 */
export async function listCheckpointMarkers(checkpointId: string): Promise<CheckpointMarker[]> {
  const response = await fetch(`${API_BASE}/${checkpointId}/markers`);
  if (!response.ok) throw new Error(`Failed to fetch markers: ${response.statusText}`);
  return response.json();
}

/**
 * 更新标记
 */
export async function updateCheckpointMarker(
  checkpointId: string,
  markerId: string,
  data: UpdateCheckpointMarkerRequest
): Promise<CheckpointMarker> {
  const response = await fetch(`${API_BASE}/${checkpointId}/markers/${markerId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to update marker: ${response.statusText}`);
  return response.json();
}

/**
 * 删除标记
 */
export async function deleteCheckpointMarker(
  checkpointId: string,
  markerId: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/${checkpointId}/markers/${markerId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(`Failed to delete marker: ${response.statusText}`);
}

/**
 * 格式化时间显示（秒转 HH:MM:SS）
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * 将 Date 对象转换为 ISO 8601 字符串
 */
export function toISO8601(date: Date): string {
  return date.toISOString();
}

/**
 * 解析 ISO 8601 字符串为 Date 对象
 */
export function parseISO8601(dateStr: string): Date {
  return new Date(dateStr);
}
