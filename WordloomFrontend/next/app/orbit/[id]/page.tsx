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

  async function onSaved(savedNote: Note) {
    await qc.invalidateQueries({ queryKey: ["orbit", "notes"] });
    await qc.invalidateQueries({ queryKey: ["orbit", "notes", "detail", id] });
    // 保存成功后跳转回列表页
    router.push("/orbit");
  }

  async function onDeleted() {
    await qc.invalidateQueries({ queryKey: ["orbit", "notes"] });
    router.push("/orbit");
  }

  if (isLoading || !note) return <main className="p-6 text-sm text-gray-500">加载中…</main>;

  return (
    <main className="max-w-6xl mx-auto px-5 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <section className="lg:col-span-2 space-y-3">
        <NoteEditor
          note={{ ...note, text }}
          onSaved={onSaved}
          onCancel={() => router.push("/orbit")}
          onDeleted={onDeleted}
        />
      </section>
    </main>
  );
}