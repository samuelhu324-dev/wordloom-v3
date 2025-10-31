/**
 * Bookshelf 相关的 React Query Hooks
 * 用于处理 Bookshelf 数据的获取、创建、更新、删除操作
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Bookshelf, BookshelfCreateRequest, BookshelfUpdateRequest, BookshelfListParams, BookshelfNotesParams } from "@/modules/orbit/domain/bookshelves";
import * as api from "@/modules/orbit/domain/api";

// Query Keys
const BOOKSHELF_KEYS = {
  all: ["bookshelves"],
  lists: () => [...BOOKSHELF_KEYS.all, "list"],
  list: (params: BookshelfListParams) => [...BOOKSHELF_KEYS.lists(), params],
  details: () => [...BOOKSHELF_KEYS.all, "detail"],
  detail: (id: string) => [...BOOKSHELF_KEYS.details(), id],
  notes: (id: string) => [...BOOKSHELF_KEYS.detail(id), "notes"],
} as const;

/**
 * 获取所有 Bookshelves
 */
export function useBookshelves(params: BookshelfListParams = {}) {
  return useQuery({
    queryKey: BOOKSHELF_KEYS.list(params),
    queryFn: () => api.listBookshelves(params),
    staleTime: 1000 * 60 * 5, // 5 分钟
  });
}

/**
 * 获取单个 Bookshelf
 */
export function useBookshelf(id: string | null | undefined) {
  return useQuery({
    queryKey: BOOKSHELF_KEYS.detail(id || ""),
    queryFn: () => api.getBookshelf(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 5, // 5 分钟
  });
}

/**
 * 获取 Bookshelf 内的 Notes
 */
export function useBookshelfNotes(
  bookshelfId: string | null | undefined,
  params: BookshelfNotesParams = {}
) {
  return useQuery({
    queryKey: [...BOOKSHELF_KEYS.notes(bookshelfId || ""), params],
    queryFn: () => api.getBookshelfNotes(bookshelfId!, params),
    enabled: !!bookshelfId,
    staleTime: 1000 * 60 * 5, // 5 分钟
  });
}

/**
 * 创建 Bookshelf
 */
export function useCreateBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BookshelfCreateRequest) => api.createBookshelf(payload),
    onSuccess: (newBookshelf) => {
      // 更新列表缓存
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
      // 添加到缓存
      queryClient.setQueryData(BOOKSHELF_KEYS.detail(newBookshelf.id), newBookshelf);
    },
  });
}

/**
 * 更新 Bookshelf
 */
export function useUpdateBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: BookshelfUpdateRequest }) =>
      api.updateBookshelf(id, payload),
    onSuccess: (updatedBookshelf, { id }) => {
      // 更新缓存
      queryClient.setQueryData(BOOKSHELF_KEYS.detail(id), updatedBookshelf);
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
    },
  });
}

/**
 * 删除 Bookshelf
 */
export function useDeleteBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, cascade }: { id: string; cascade?: "orphan" | "delete" }) =>
      api.deleteBookshelf(id, cascade),
    onSuccess: (_, { id }) => {
      // 删除详情缓存
      queryClient.removeQueries({ queryKey: BOOKSHELF_KEYS.detail(id) });
      // 删除 Notes 缓存
      queryClient.removeQueries({ queryKey: BOOKSHELF_KEYS.notes(id) });
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
    },
  });
}

/**
 * 添加 Note 到 Bookshelf
 */
export function useAddNoteToBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookshelfId, noteId }: { bookshelfId: string; noteId: string }) =>
      api.addNoteToBookshelf(bookshelfId, noteId),
    onSuccess: (_, { bookshelfId }) => {
      // 更新 Bookshelf 详情
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.detail(bookshelfId) });
      // 更新 Notes 列表
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.notes(bookshelfId) });
      // 更新所有列表
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
    },
  });
}

/**
 * 从 Bookshelf 移除 Note
 */
export function useRemoveNoteFromBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookshelfId, noteId }: { bookshelfId: string; noteId: string }) =>
      api.removeNoteFromBookshelf(bookshelfId, noteId),
    onSuccess: (_, { bookshelfId }) => {
      // 更新 Bookshelf 详情
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.detail(bookshelfId) });
      // 更新 Notes 列表
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.notes(bookshelfId) });
      // 更新所有列表
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
    },
  });
}

/**
 * 转移 Note 到另一个 Bookshelf
 */
export function useMoveNoteToBookshelf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ noteId, targetBookshelfId }: { noteId: string; targetBookshelfId: string }) =>
      api.moveNoteToBookshelf(noteId, targetBookshelfId),
    onSuccess: (_, { noteId, targetBookshelfId }) => {
      // 更新所有 Bookshelf 缓存
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.lists() });
      queryClient.invalidateQueries({ queryKey: BOOKSHELF_KEYS.details() });
    },
  });
}

/**
 * 增加 Bookshelf 使用次数
 */
export function useIncrementBookshelfUsage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bookshelfId: string) => api.incrementBookshelfUsage(bookshelfId),
    onSuccess: (updatedBookshelf, bookshelfId) => {
      // 更新缓存
      queryClient.setQueryData(BOOKSHELF_KEYS.detail(bookshelfId), updatedBookshelf);
    },
  });
}
