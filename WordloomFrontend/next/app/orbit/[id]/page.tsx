"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { getNote } from "@/modules/orbit/api";
import type { Note } from "@/modules/orbit/api";
import NoteEditor from "@/modules/orbit/services/NoteEditor";

export default function NoteDetailPage() {
  const { id } = useParams<{ id: string }>() as { id: string };
  const router = useRouter();
  const qc = useQueryClient();

  const { data: note, isLoading } = useQuery({
    queryKey: ["orbit", "notes", "detail", id],
    queryFn: () => getNote(id),
    enabled: Boolean(id),
  });

  const [text, setText] = useState("");

  useEffect(() => {
    setText(note?.text ?? "");
  }, [note?.id, note?.text]);

  async function onSaved(savedNote: Note, shouldReturnToShelf?: boolean) {
    // 合并更新的数据
    if (note) {
      Object.assign(note, savedNote);
    }

    // 刷新查询缓存
    await qc.invalidateQueries({ queryKey: ["orbit", "notes"] });
    await qc.invalidateQueries({ queryKey: ["orbit", "notes", "detail", id] });

    if (savedNote.bookshelfId) {
      await qc.invalidateQueries({ queryKey: ["bookshelves", savedNote.bookshelfId, "notes"] });
    }

    // 如果需要，返回到书架
    if (shouldReturnToShelf) {
      if (savedNote.bookshelfId) {
        router.push(`/orbit/bookshelves/${savedNote.bookshelfId}`);
      } else {
        router.push("/orbit");
      }
    }
  }

  async function onDeleted() {
    await qc.invalidateQueries({ queryKey: ["orbit", "notes"] });
    // 如果有所属书架，返回到书架详情页；否则返回主列表
    if (note?.bookshelfId) {
      router.push(`/orbit/bookshelves/${note.bookshelfId}`);
    } else {
      router.push("/orbit");
    }
  }

  if (isLoading || !note) return <main className="p-6 text-sm text-gray-500">加载中…</main>;

  return (
    <main className="max-w-6xl mx-auto px-5 py-6">
      <NoteEditor
        note={{ ...note, text }}
        onSaved={onSaved}
        onCancel={() => {
          // 如果有所属书架，返回到书架详情页；否则返回主列表
          if (note?.bookshelfId) {
            router.push(`/orbit/bookshelves/${note.bookshelfId}`);
          } else {
            router.push("/orbit");
          }
        }}
        onDeleted={onDeleted}
      />
    </main>
  );
}