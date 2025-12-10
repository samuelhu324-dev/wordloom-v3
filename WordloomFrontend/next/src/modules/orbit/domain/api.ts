"use client";
import { apiFetch } from "@/lib/api";
import { ORBIT_BASE, ORBIT_UPLOADS } from "@/lib/apiBase";
import type { Note, NoteListParams, Tag } from "./notes";
import type { Bookshelf, BookshelfCreateRequest, BookshelfUpdateRequest, BookshelfListParams, BookshelfNotesParams, BookshelfResponse } from "./bookshelves";
import { transformBookshelfResponse, transformBookshelfToRequest } from "./bookshelves";

const NOTES_BASE = `${ORBIT_BASE}/notes`;
const BOOKSHELVES_BASE = `${ORBIT_BASE}/bookshelves`;

type RawTag = {
  id: string;
  name: string;
  color: string;
  icon?: string | null;
  description?: string | null;
  count?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

type RawNote = {
  id: string;
  title?: string | null;
  summary?: string | null;  // 新增：Note摘要/描述
  content_md?: string | null;
  blocks_json?: string | null;  // 新增：JSON格式的blocks数组
  status?: string | null;
  priority?: number | null;
  urgency?: number | null;
  usage_level?: number | null;
  usage_count?: number | null;
  tags?: string[] | null;
  tags_rel?: RawTag[] | null;
  bookshelf_id?: string | null;  // 新增：书架ID
  preview_image?: string | null;  // 新增：预览图片 URL
  preview_text?: string | null;  // 新增：预览文本
  storage_path?: string | null;  // 新增：存储路径
  bookshelf_tag?: { id: string; name: string; color?: string; icon?: string } | null;  // 新增：书架标签
  is_pinned?: boolean | null;  // 新增：是否置顶
  pinned_at?: string | null;  // 新增：置顶时间
  cover_image_url?: string | null;  // 新增：封面图 URL
  cover_image_display_width?: number | null;  // 新增：封面图显示宽度
  due_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

/**
 * 清理 HTML 标签和实体
 */
function stripHtmlTags(html: string): string {
  if (!html) return '';
  return html
    .replace(/<[^>]*>/g, '')           // 移除所有 HTML 标签
    .replace(/&lt;/g, '<')              // 转换 HTML 实体
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')            // 非断行空格转为普通空格
    .trim();
}

const toClient = (n: RawNote): Note => {
  const tagsRel: Tag[] | undefined = n.tags_rel
    ? n.tags_rel.map((t) => ({
        id: t.id,
        name: t.name,
        color: t.color,
        icon: t.icon ?? null,
        description: t.description ?? undefined,
        count: t.count ?? 0,
        createdAt: t.created_at ?? undefined,
        updatedAt: t.updated_at ?? undefined,
      }))
    : undefined;

  // 不在这里清理HTML - 保留原始content_md内容
  // stripHtmlTags应该只在显示/预览时使用，不应该在数据映射时使用
  const text = n.content_md ?? '';

  return {
    id: n.id,
    title: n.title ?? null,
    summary: n.summary ?? null,  // 新增：Note摘要/描述
    text: text,
    blocksJson: n.blocks_json ?? null,  // 新增：JSON格式的blocks
    status: n.status ?? "open",
    priority: n.priority ?? 3,
    urgency: n.urgency ?? 3,
    usageLevel: n.usage_level ?? 3,
    usageCount: n.usage_count ?? 0,
    tags: n.tags ?? [],
    tagsRel,
    bookshelfId: n.bookshelf_id ?? null,  // 新增：书架ID
    previewImage: n.preview_image ?? undefined,  // 新增：预览图片
    previewText: n.preview_text ?? undefined,  // 新增：预览文本
    storagePath: n.storage_path ?? undefined,  // 新增：存储路径
    bookshelfTag: n.bookshelf_tag ?? undefined,  // 新增：书架标签
    isPinned: n.is_pinned ?? false,  // 新增：是否置顶
    pinnedAt: n.pinned_at ?? null,  // 新增：置顶时间
    cover_image_url: n.cover_image_url ?? null,  // 新增：封面图 URL
    cover_image_display_width: n.cover_image_display_width ?? 200,  // 新增：封面图显示宽度
    dueAt: n.due_at ?? null,
    createdAt: n.created_at ?? null,
    updatedAt: n.updated_at ?? null,
  };
};

const toServer = (n: Partial<Note>) => {
  const obj: any = {
    title: n.title ?? undefined,
    summary: n.summary ?? undefined,  // 新增：Note摘要/描述
    content_md: n.text ?? undefined,
    blocks_json: n.blocksJson ?? undefined,  // 新增：JSON格式的blocks
    status: n.status ?? undefined,
    priority: n.priority ?? undefined,
    urgency: n.urgency ?? undefined,
    // 注意：不发送 usage_level 和 usageCount，这些是只读的
    due_at: n.dueAt ?? undefined,
    tags: Array.isArray(n.tags)
      ? n.tags
      : typeof (n as any)?.tags === "string"
      ? String((n as any).tags).split(",").map(s => s.trim()).filter(Boolean)
      : undefined,
  };

  // 显式包含 bookshelf_id，即使为 null/undefined
  if (n.bookshelfId !== undefined) {
    obj.bookshelf_id = n.bookshelfId;
  }

  // 封面图字段
  if (n.cover_image_url !== undefined) {
    obj.cover_image_url = n.cover_image_url;
  }
  if (n.cover_image_display_width !== undefined) {
    obj.cover_image_display_width = n.cover_image_display_width;
  }

  return obj;
};

export async function listNotes(params: NoteListParams = {}): Promise<Note[]> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.tag) qs.set("tag", params.tag);
  if (params.status) qs.set("status", params.status);
  if (params.sort) qs.set("sort", params.sort);
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));
  const url = qs.toString() ? `${NOTES_BASE}?${qs.toString()}` : NOTES_BASE;
  const list = await apiFetch<RawNote[]>(url);
  return list.map(toClient);
}

export async function getNote(id: string): Promise<Note> {
  console.log('[API] getNote: fetching', { id });
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}`);
  console.log('[API] getNote: raw response from backend:', n);
  console.log('[API] getNote: cover_image_url in raw response:', n.cover_image_url);
  const result = toClient(n);
  console.log('[API] getNote: after toClient conversion:', { cover_image_url: result.cover_image_url });
  return result;
}

export async function createNote(payload: Partial<Note>): Promise<Note> {
  const n = await apiFetch<RawNote>(NOTES_BASE, { method: "POST", body: toServer(payload) as any });
  return toClient(n);
}

export async function updateNote(id: string, payload: Partial<Note>): Promise<Note> {
  console.log('[API] updateNote: sending to backend:', { id, payload });
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}`, { method: "PUT", body: toServer(payload) as any });
  console.log('[API] updateNote: raw response from backend:', n);
  console.log('[API] updateNote: cover_image_url in raw response:', n.cover_image_url);
  console.log('[API] updateNote: cover_image_display_width in raw response:', n.cover_image_display_width);
  const result = toClient(n);
  console.log('[API] updateNote: after toClient conversion:', { cover_image_url: result.cover_image_url });
  return result;
}

export async function deleteNote(id: string): Promise<void> {
  await apiFetch(`${NOTES_BASE}/${id}`, { method: "DELETE" });
}

export async function quickCapture(payload: {
  title?: string;
  content?: string;
  url?: string;
  selection?: string;
  tags?: string[];
  bookshelfId?: string;  // 新增：书架ID参数
}): Promise<Note> {
  const body = {
    title: payload.title,
    content: payload.content,
    url: payload.url,
    selection: payload.selection,
    tags: payload.tags,
    bookshelf_id: payload.bookshelfId,  // 转换为 snake_case
  };
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/quick-capture`, { method: "POST", body: body as any });
  return toClient(n);
}

export async function uploadImage(file: File, noteId: string): Promise<{ url: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const response = await apiFetch<{ url: string }>(`${ORBIT_UPLOADS}?note_id=${noteId}`, { method: "POST", body: fd });

  // 后端返回的是相对于根路径的路径 /uploads/{noteId}/{filename}
  // 这个路径在后端根应用上，不在 /api/orbit 下
  // 所以需要转换为完整的 URL（不加 ORBIT_BASE 前缀）
  if (response.url) {
    if (!response.url.startsWith('http')) {
      // 直接使用这个相对路径，浏览器会访问 http://localhost:18080/uploads/{noteId}/{filename}
      // 确保添加服务器地址前缀，使其成为绝对 URL
      const origin = window.location.origin.replace(':3000', ':18080'); // 从前端地址改为后端地址
      response.url = `${origin}${response.url}`;
    }
  }

  return response;
}

export async function incrementNoteUsage(id: string): Promise<Note> {
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}/increment-usage`, { method: "POST" });
  return toClient(n);
}

export async function duplicateNote(id: string, titleSuffix: string = "(副本)"): Promise<Note> {
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}/duplicate`, {
    method: "POST",
    body: { title_suffix: titleSuffix } as any,
  });
  return toClient(n);
}

/**
 * ========== Bookshelf API 函数 ==========
 */

// 列出所有 Bookshelves
export async function listBookshelves(params: BookshelfListParams = {}): Promise<Bookshelf[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.sortBy) qs.set("sort_by", params.sortBy);
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));

  const url = qs.toString() ? `${BOOKSHELVES_BASE}?${qs.toString()}` : BOOKSHELVES_BASE;
  const list = await apiFetch<BookshelfResponse[]>(url);
  return list.map(transformBookshelfResponse);
}

// 获取单个 Bookshelf
export async function getBookshelf(id: string): Promise<Bookshelf> {
  const data = await apiFetch<BookshelfResponse>(`${BOOKSHELVES_BASE}/${id}`);
  return transformBookshelfResponse(data);
}

// 创建 Bookshelf
export async function createBookshelf(payload: BookshelfCreateRequest): Promise<Bookshelf> {
  const body = transformBookshelfToRequest(payload);
  const data = await apiFetch<BookshelfResponse>(BOOKSHELVES_BASE, { method: "POST", body } as any);
  return transformBookshelfResponse(data);
}

// 更新 Bookshelf
export async function updateBookshelf(id: string, payload: BookshelfUpdateRequest): Promise<Bookshelf> {
  const body = transformBookshelfToRequest(payload as BookshelfCreateRequest);
  const data = await apiFetch<BookshelfResponse>(`${BOOKSHELVES_BASE}/${id}`, { method: "PUT", body } as any);
  return transformBookshelfResponse(data);
}

// 删除 Bookshelf
export async function deleteBookshelf(id: string, cascade: "orphan" | "delete" = "orphan"): Promise<void> {
  await apiFetch(`${BOOKSHELVES_BASE}/${id}?cascade=${cascade}`, { method: "DELETE" });
}

// 获取 Bookshelf 内的 Notes
export async function getBookshelfNotes(
  bookshelfId: string,
  params: BookshelfNotesParams = {}
): Promise<Note[]> {
  const qs = new URLSearchParams();
  if (params.sortBy) qs.set("sort_by", params.sortBy);
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));

  const url = qs.toString()
    ? `${BOOKSHELVES_BASE}/${bookshelfId}/notes?${qs.toString()}`
    : `${BOOKSHELVES_BASE}/${bookshelfId}/notes`;

  const list = await apiFetch<RawNote[]>(url);

  // 调试：打印原始数据
  console.log('[API] getBookshelfNotes 原始数据:', {
    url,
    dataCount: list.length,
    firstNote: list[0] ? {
      id: list[0].id,
      title: list[0].title,
      preview_image: (list[0] as any).preview_image,
      blocksJson: list[0].blocks_json,
    } : null,
  });

  return list.map(toClient);
}

// 添加 Note 到 Bookshelf
export async function addNoteToBookshelf(bookshelfId: string, noteId: string): Promise<{ success: boolean; message: string; note_id: string }> {
  return apiFetch(`${BOOKSHELVES_BASE}/${bookshelfId}/notes/${noteId}`, { method: "POST" });
}

// 从 Bookshelf 移除 Note
export async function removeNoteFromBookshelf(bookshelfId: string, noteId: string): Promise<void> {
  await apiFetch(`${BOOKSHELVES_BASE}/${bookshelfId}/notes/${noteId}`, { method: "DELETE" });
}

// 转移 Note 到另一个 Bookshelf
export async function moveNoteToBookshelf(noteId: string, targetBookshelfId: string): Promise<{ success: boolean; message: string; note_id: string; bookshelf_id: string }> {
  return apiFetch(`${NOTES_BASE}/${noteId}/move-to-bookshelf`, {
    method: "POST",
    body: { target_bookshelf_id: targetBookshelfId } as any,
  });
}

// 增加 Bookshelf 使用次数
export async function incrementBookshelfUsage(bookshelfId: string): Promise<Bookshelf> {
  const data = await apiFetch<BookshelfResponse>(`${BOOKSHELVES_BASE}/${bookshelfId}/increment-usage`, { method: "POST" });
  return transformBookshelfResponse(data);
}

// 上传书橱封面图
export async function uploadBookshelfCover(bookshelfId: string, file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${ORBIT_BASE}/bookshelf-cover?bookshelf_id=${bookshelfId}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to upload bookshelf cover: ${response.statusText}`);
  }

  return response.json();
}

// 置顶 Bookshelf
export async function pinBookshelf(bookshelfId: string): Promise<Bookshelf> {
  const data = await apiFetch<BookshelfResponse>(`${BOOKSHELVES_BASE}/${bookshelfId}/pin`, { method: "POST" });
  return transformBookshelfResponse(data);
}

// 取消置顶 Bookshelf
export async function unpinBookshelf(bookshelfId: string): Promise<Bookshelf> {
  const data = await apiFetch<BookshelfResponse>(`${BOOKSHELVES_BASE}/${bookshelfId}/unpin`, { method: "POST" });
  return transformBookshelfResponse(data);
}

// 置顶 Note
export async function pinNote(noteId: string): Promise<Note> {
  const data = await apiFetch<RawNote>(`${NOTES_BASE}/${noteId}/pin`, { method: "POST" });
  return toClient(data);
}

// 取消置顶 Note
export async function unpinNote(noteId: string): Promise<Note> {
  const data = await apiFetch<RawNote>(`${NOTES_BASE}/${noteId}/unpin`, { method: "POST" });
  return toClient(data);
}

/**
 * ========== 业界标准临时文件上传 API ==========
 *
 * 流程：
 * 1. uploadTempImage(file) - 上传到 temp 目录，立即返回临时 URL
 * 2. 用户在编辑器中看到图片
 * 3. finalizeTemporaryImages(noteId, tempUrls) - 保存笔记后，文件移动到永久目录
 */

export async function uploadTempImage(file: File): Promise<{ url: string; temp_id: string; size: number }> {
  const fd = new FormData();
  fd.append("file", file);

  const response = await apiFetch<{ url: string; temp_id: string; size: number }>(
    `${ORBIT_UPLOADS}/temp`,
    { method: "POST", body: fd }
  );

  // 转换临时 URL 为完整 URL
  if (response.url) {
    if (!response.url.startsWith('http')) {
      const origin = window.location.origin.replace(':3000', ':18080');
      response.url = `${origin}${response.url}`;
    }
  }

  return response;
}

export async function finalizeTemporaryImages(
  noteId: string,
  tempUrls: string[]
): Promise<{ status: string; finalized: Record<string, string> }> {
  // 转换回相对路径进行发送
  const relativeUrls = tempUrls.map(url => {
    if (url.startsWith('http')) {
      return url.replace(/^https?:\/\/[^/]+/, '');
    }
    return url;
  });

  const response = await apiFetch<{ status: string; finalized: Record<string, string> }>(
    `${ORBIT_UPLOADS}/finalize`,
    {
      method: "POST",
      body: { note_id: noteId, temp_urls: relativeUrls } as any,
    }
  );

  // 转换响应中的相对 URL 为完整 URL
  if (response.finalized) {
    const finalized: Record<string, string> = {};
    for (const [tempUrl, finalUrl] of Object.entries(response.finalized)) {
      let finalUrlAbs = finalUrl;
      if (!finalUrl.startsWith('http')) {
        const origin = window.location.origin.replace(':3000', ':18080');
        finalUrlAbs = `${origin}${finalUrl}`;
      }

      // 恢复原始 tempUrl 的完整形式
      let tempUrlAbs = tempUrl;
      if (!tempUrl.startsWith('http')) {
        const origin = window.location.origin.replace(':3000', ':18080');
        tempUrlAbs = `${origin}${tempUrl}`;
      }

      finalized[tempUrlAbs] = finalUrlAbs;
    }
    response.finalized = finalized;
  }

  return response;
}

