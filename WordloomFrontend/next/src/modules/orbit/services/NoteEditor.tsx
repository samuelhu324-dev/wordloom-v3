"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { createNote, updateNote, deleteNote } from "@/modules/orbit/domain/api";
import { generateDiagram } from "@/modules/orbit/domain/diagrams";
import type { Note, Tag } from "@/modules/orbit/domain/notes";
import { MermaidDiagram } from "@/modules/orbit/ui/MermaidDiagram";

// 动态加载编辑器，禁用 SSR
const RichTextEditor = dynamic(
  () => import("@/modules/orbit/ui/RichTextEditor"),
  { ssr: false, loading: () => <div className="p-3 border rounded bg-gray-50">加载编辑器中...</div> }
);

// 动态加载标签选择器
const TagSelector = dynamic(
  () => import("@/modules/orbit/ui/TagSelector").then(mod => mod.TagSelector),
  { ssr: false, loading: () => <div className="p-3 border rounded bg-gray-50">加载标签面板中...</div> }
);

export default function NoteEditor({
  note,
  onSaved,
  onCancel,
  onDeleted
}: {
  note?: Note;
  onSaved?: (n: Note) => void;
  onCancel?: () => void;
  onDeleted?: () => void;
}) {
  const [title, setTitle] = useState(note?.title ?? "");
  const [text, setText] = useState(note?.text ?? "");
  const [tags, setTags] = useState<Tag[]>(note?.tagsRel ?? []);
  const [status, setStatus] = useState(note?.status ?? "open");
  const [priority, setPriority] = useState(note?.priority ?? 3);
  const [urgency, setUrgency] = useState<number>(note?.urgency ?? 3);
  const [usageLevel, setUsageLevel] = useState<number>(note?.usageLevel ?? 3);
  const [usageCount, setUsageCount] = useState<number>(note?.usageCount ?? 0);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [generatingDiagram, setGeneratingDiagram] = useState(false);
  const [diagramCode, setDiagramCode] = useState<string | null>(null);
  const [showDiagram, setShowDiagram] = useState(false);
  const isEdit = Boolean(note?.id);

  // 当 note 数据更新时，同步所有状态
  useEffect(() => {
    if (note) {
      setTitle(note.title ?? "");
      setText(note.text ?? "");
      setTags(note.tagsRel ?? []);
      setStatus(note.status ?? "open");
      setPriority(note.priority ?? 3);
      setUrgency(note.urgency ?? 3);
      setUsageLevel(note.usageLevel ?? 3);
      setUsageCount(note.usageCount ?? 0);
    }
  }, [note?.id, note]);

  async function onSubmit() {
    setSaving(true);
    try {
      const payload: Partial<Note> = {
        title: title || null,
        text,
        tags: tags.map(t => t.name),
        status,
        priority,
        urgency,
        // 注意：不发送 usageLevel 和 usageCount，这些是只读的
      };
      const saved = isEdit && note ? await updateNote(note.id, payload) : await createNote(payload);
      onSaved?.(saved);
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteNote() {
    if (!isEdit || !note) return;
    if (!confirm("确定删除这个 Note 吗？此操作不可撤销。")) return;

    setDeleting(true);
    try {
      await deleteNote(note.id);
      onDeleted?.();
    } finally {
      setDeleting(false);
    }
  }

  async function onGenerateDiagram() {
    if (!isEdit || !note?.id || !text) return;

    setGeneratingDiagram(true);
    try {
      const result = await generateDiagram(note.id, "auto");
      setDiagramCode(result.mermaid_code);
      setShowDiagram(true);
    } catch (err) {
      console.error("Failed to generate diagram:", err);
      alert("生成结构图失败，请检查网络连接或稍后重试");
    } finally {
      setGeneratingDiagram(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs text-gray-600 mb-1">标题</label>
        <input
          className="w-full rounded border p-2"
          placeholder="Title"
          value={title ?? ""}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      <div>
        <label className="block text-xs text-gray-600 mb-1">内容</label>
        <RichTextEditor
          value={text}
          onChange={setText}
          placeholder="Write markdown..."
          noteId={note?.id}
        />
      </div>

      <div>
        <label className="block text-xs text-gray-600 mb-1">标签</label>
        <TagSelector
          selectedTags={tags}
          onTagsChange={setTags}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div>
          <label className="block text-xs text-gray-600 mb-1">状态</label>
          <select
            className="w-full rounded border p-2 text-sm"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="open">待办 (open)</option>
            <option value="done">完成 (done)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">重要程度 (1-5)</label>
          <select
            className="w-full rounded border p-2 text-sm"
            value={priority}
            onChange={(e) => setPriority(parseInt(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">紧急程度 (1-5)</label>
          <select
            className="w-full rounded border p-2 text-sm"
            value={urgency}
            onChange={(e) => setUrgency(parseInt(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">使用次数</label>
          <div className="w-full rounded border p-2 text-sm bg-gray-100 text-gray-600">
            {usageCount}
          </div>
        </div>
      </div>

      <div className="flex gap-2 pt-4 border-t">
        <button
          onClick={onSubmit}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "保存中…" : "保存"}
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
        >
          取消
        </button>
        {isEdit && (
          <>
            <button
              onClick={onGenerateDiagram}
              disabled={generatingDiagram || !text}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
              title="使用 AI 生成结构图"
            >
              {generatingDiagram ? "生成中…" : "📊 生成结构图"}
            </button>
          </>
        )}
        {isEdit && (
          <button
            onClick={onDeleteNote}
            disabled={deleting}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 ml-auto"
          >
            {deleting ? "删除中…" : "删除"}
          </button>
        )}
      </div>

      {/* 结构图显示区域 */}
      {showDiagram && diagramCode && (
        <div className="mt-6 p-4 border rounded bg-purple-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">📊 自动生成的结构图</h3>
            <button
              onClick={() => setShowDiagram(false)}
              className="text-gray-500 hover:text-gray-700 text-lg"
            >
              ✕
            </button>
          </div>
          <MermaidDiagram code={diagramCode} title="Note 结构" />
        </div>
      )}
    </div>
  );
}