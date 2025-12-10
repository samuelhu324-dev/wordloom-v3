/**
 * Orbit Tags API - 前端标签管理接口
 *
 * 功能：
 * - 获取标签列表（支持排序和搜索）
 * - 创建、编辑、删除标签
 * - 获取标签统计
 */

"use client";
import { apiFetch } from "@/lib/api";
import { ORBIT_BASE } from "@/lib/apiBase";
import type { Tag } from "./notes";

const TAGS_BASE = `${ORBIT_BASE}/tags`;

// ============================================================================
// 类型定义
// ============================================================================

export type TagSort = "frequency" | "alphabetic" | "recent";

export interface RawTag {
  id: string;
  name: string;
  color: string;
  icon?: string | null;
  description?: string | null;
  count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TagStatsResponse {
  total_tags: number;
  total_usages: number;
  top_5_tags: Array<{ name: string; count: number; color: string }>;
}

// ============================================================================
// 数据转换
// ============================================================================

const toClient = (t: RawTag): Tag => ({
  id: t.id,
  name: t.name,
  color: t.color,
  icon: t.icon ?? null,
  description: t.description ?? null,
  count: t.count,
  createdAt: t.created_at ?? null,
  updatedAt: t.updated_at ?? null,
});

// ============================================================================
// API 调用
// ============================================================================

/**
 * 获取标签列表
 * @param sort 排序方式: frequency(频率) | alphabetic(字母) | recent(最新)
 * @param search 搜索标签名称
 * @param limit 返回数量
 * @param offset 分页偏移
 */
export async function listTags(
  sort: TagSort = "frequency",
  search?: string,
  limit: number = 100,
  offset: number = 0
): Promise<Tag[]> {
  const qs = new URLSearchParams();
  qs.set("sort", sort);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (search) qs.set("search", search);

  const url = `${TAGS_BASE}?${qs.toString()}`;
  const tags = await apiFetch<RawTag[]>(url);
  return tags.map(toClient);
}

/**
 * 获取单个标签详情
 */
export async function getTag(id: string): Promise<Tag> {
  const t = await apiFetch<RawTag>(`${TAGS_BASE}/${id}`);
  return toClient(t);
}

/**
 * 创建新标签
 */
export async function createTag(payload: {
  name: string;
  color?: string;
  icon?: string | null;
  description?: string;
}): Promise<Tag> {
  const t = await apiFetch<RawTag>(TAGS_BASE, {
    method: "POST",
    body: {
      name: payload.name,
      color: payload.color || "#808080",
      icon: payload.icon ?? null,
      description: payload.description || null,
    } as any,
  });
  return toClient(t);
}

/**
 * 编辑标签
 */
export async function updateTag(
  id: string,
  payload: Partial<{
    name: string;
    color: string;
    icon: string | null;
    description: string;
  }>
): Promise<Tag> {
  const t = await apiFetch<RawTag>(`${TAGS_BASE}/${id}`, {
    method: "PUT",
    body: payload as any,
  });
  return toClient(t);
}

/**
 * 删除标签
 */
export async function deleteTag(id: string): Promise<void> {
  await apiFetch(`${TAGS_BASE}/${id}`, { method: "DELETE" });
}

/**
 * 获取标签统计信息
 */
export async function getTagStats(): Promise<TagStatsResponse> {
  return apiFetch<TagStatsResponse>(`${TAGS_BASE}/stats/summary`);
}
