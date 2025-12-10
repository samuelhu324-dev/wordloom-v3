/**
 * Bookshelf (书架) 类型定义
 * 用于 Note 分类组织的容器
 */

import { Note } from './notes';

/**
 * Bookshelf 基础类型
 */
export type Bookshelf = {
  id: string;
  name: string;
  description?: string | null;
  coverUrl?: string | null;
  icon?: string | null;
  priority: number; // 1-5，默认 3
  urgency: number; // 1-5，默认 3
  usageCount: number; // 使用次数
  noteCount: number; // 包含的 Note 数量
  status: 'active' | 'archived' | 'deleted';
  tags: string[]; // 标签数组
  color?: string | null; // 颜色代码
  isFavorite: boolean; // 是否收藏
  isPinned: boolean; // 是否置顶
  pinnedAt?: string | null; // 置顶时间
  createdAt?: string | null;
  updatedAt?: string | null;
};

/**
 * Bookshelf 创建请求
 */
export type BookshelfCreateRequest = {
  name: string;
  description?: string;
  coverUrl?: string;
  icon?: string;
  priority?: number;
  urgency?: number;
  tags?: string[];
  color?: string;
  isFavorite?: boolean;
};

/**
 * Bookshelf 更新请求
 */
export type BookshelfUpdateRequest = Partial<BookshelfCreateRequest>;

/**
 * Bookshelf 详情响应（包含 Notes）
 */
export type BookshelfDetail = Bookshelf & {
  notes?: Note[];
};

/**
 * 将 Note 移动到 Bookshelf 的请求
 */
export type MoveNoteRequest = {
  targetBookshelfId: string;
};

/**
 * Bookshelf 列表查询参数
 */
export type BookshelfListParams = {
  status?: 'active' | 'archived' | 'deleted' | 'all';
  sortBy?: 'name' | '-name' | 'priority' | '-priority' | 'created_at' | '-created_at' | 'note_count' | '-note_count' | 'updated_at' | '-updated_at';
  limit?: number;
  offset?: number;
};

/**
 * Bookshelf 内 Notes 列表查询参数
 */
export type BookshelfNotesParams = {
  sortBy?: 'name' | '-name' | 'created_at' | '-created_at' | 'updated_at' | '-updated_at' | 'priority' | '-priority';
  limit?: number;
  offset?: number;
};

/**
 * API 响应类型
 */
export type BookshelfResponse = {
  id: string;
  name: string;
  description?: string | null;
  cover_url?: string | null;
  icon?: string | null;
  priority: number;
  urgency: number;
  usage_count: number;
  note_count: number;
  status: string;
  tags: string[];
  color?: string | null;
  is_favorite: boolean;
  is_pinned?: boolean;
  pinned_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

/**
 * 为图片URL添加时间戳，强制浏览器刷新缓存
 * 如果URL已有时间戳，则更新；否则添加新的
 */
function addCacheBuster(url: string | null | undefined): string | null | undefined {
  if (!url) return url;

  // 如果URL中已有时间戳查询参数，替换为新的
  if (url.includes('?t=')) {
    return url.replace(/\?t=\d+/, `?t=${Date.now()}`);
  }

  // 否则添加新的时间戳
  return `${url}?t=${Date.now()}`;
}

/**
 * 转换 API 响应为前端类型
 */
export function transformBookshelfResponse(data: BookshelfResponse): Bookshelf {
  return {
    id: data.id,
    name: data.name,
    description: data.description,
    coverUrl: addCacheBuster(data.cover_url),  // 添加时间戳
    icon: data.icon,
    priority: data.priority,
    urgency: data.urgency,
    usageCount: data.usage_count,
    noteCount: data.note_count,
    status: data.status as 'active' | 'archived' | 'deleted',
    tags: data.tags || [],
    color: data.color,
    isFavorite: data.is_favorite,
    isPinned: data.is_pinned || false,
    pinnedAt: data.pinned_at,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换前端类型为 API 请求格式
 */
export function transformBookshelfToRequest(bookshelf: BookshelfCreateRequest): Record<string, any> {
  return {
    name: bookshelf.name,
    description: bookshelf.description,
    cover_url: bookshelf.coverUrl,
    icon: bookshelf.icon,
    priority: bookshelf.priority,
    urgency: bookshelf.urgency,
    tags: bookshelf.tags,
    color: bookshelf.color,
    is_favorite: bookshelf.isFavorite,
  };
}
