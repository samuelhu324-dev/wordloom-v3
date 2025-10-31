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
  content_md?: string | null;
  status?: string | null;
  priority?: number | null;
  urgency?: number | null;
  usage_level?: number | null;
  usage_count?: number | null;
  tags?: string[] | null;
  tags_rel?: RawTag[] | null;
  due_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

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

  return {
    id: n.id,
    title: n.title ?? null,
    text: n.content_md ?? "",
    status: n.status ?? "open",
    priority: n.priority ?? 3,
    urgency: n.urgency ?? 3,
    usageLevel: n.usage_level ?? 3,
    usageCount: n.usage_count ?? 0,
    tags: n.tags ?? [],
    tagsRel,
    dueAt: n.due_at ?? null,
    createdAt: n.created_at ?? null,
    updatedAt: n.updated_at ?? null,
  };
};

const toServer = (n: Partial<Note>) => ({
  title: n.title ?? undefined,
  content_md: n.text ?? undefined,
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
});

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
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}`);
  return toClient(n);
}

export async function createNote(payload: Partial<Note>): Promise<Note> {
  const n = await apiFetch<RawNote>(NOTES_BASE, { method: "POST", body: toServer(payload) as any });
  return toClient(n);
}

export async function updateNote(id: string, payload: Partial<Note>): Promise<Note> {
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/${id}`, { method: "PUT", body: toServer(payload) as any });
  return toClient(n);
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
}): Promise<Note> {
  const n = await apiFetch<RawNote>(`${NOTES_BASE}/quick-capture`, { method: "POST", body: payload as any });
  return toClient(n);
}

export async function uploadImage(file: File, noteId: string): Promise<{ url: string }> {
  const fd = new FormData();
  fd.append("file", file);
  return apiFetch<{ url: string }>(`${ORBIT_UPLOADS}?note_id=${noteId}`, { method: "POST", body: fd });
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
